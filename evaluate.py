"""Run supplied 15-case dev set against Azure; review semantic answer quality manually.

Outputs artifacts/dev-evaluation.json and artifacts/dev-evaluation.md (no secrets).
"""
import json
from datetime import date
from pathlib import Path
from openai import OpenAI
from ask import ROOT, ARTIFACTS, ENDPOINT, get_api_key, load_index, run_query, determine_target


def as_markdown(row):
    mark = lambda value: 'Yes' if value else 'No'
    return (f"| {row['id']} | {row['outcome']} | "
            f"{mark(row['has_any_gold_retrieval']) if row['expected_behavior']=='answer' else 'N/A'} | "
            f"{', '.join(row['review_flags']) or '-'} | Pending human review |")


def main():
    dev_path = ROOT/'data'/'eval'/'dev_set.jsonl'
    cases = [json.loads(line) for line in dev_path.read_text(encoding='utf-8-sig').splitlines() if line.strip()]
    print(f'Running {len(cases)} official dev questions. Your Azure account will be billed per call.')
    key=get_api_key()
    index=load_index()
    results=[]
    with OpenAI(base_url=ENDPOINT, api_key=key,timeout=60,max_retries=1) as client:
        for case in cases:
            asker=case['asker']
            target=determine_target(case['input'],asker)
            # DEV-09 manager asks about NH-2610; DEV-14 unauthorized request declines.
            try:
                result=run_query(asker,target,case['input'],date.fromisoformat(case['today']),
                                 client=client,index=index,verbose=False)
            except Exception as exc:
                result={'outcome':'error','answer':str(exc),'evidence':[],'retrieved_chunks':[]}
            paths={s['file_path'] for s in result.get('retrieved_chunks',[])}
            gold_documents=[g.split(' (')[0] for g in case.get('gold_sources',[])
                            if not g.startswith('hris/') and g!='policy_register.csv']
            found=[path for path in gold_documents if path in paths]
            flags=[]
            answer=result['answer']
            for phrase in case.get('must_not',[]):
                if phrase.lower() in answer.lower():
                    flags.append('review prohibited phrase: '+phrase)
            if case['expected_behavior']=='decline' and result['outcome']!='declined':
                flags.append('EXPECTED REFUSAL MISSING')
            if result['outcome']=='error': flags.append('runtime error')
            row={'id':case['id'],'category':case['category'],'expected_behavior':case['expected_behavior'],
                 'asker':asker,'target':target,'outcome':result['outcome'],
                 'question':case['input'],'answer':answer,
                 'gold_points':case.get('gold_points',[]),'gold_sources':case.get('gold_sources',[]),
                 'retrieved_files':sorted(paths),'retrieved_gold_documents':found,
                 'has_any_gold_retrieval':bool(found),
                 'all_gold_documents_retrieved':bool(gold_documents) and len(found)==len(gold_documents),
                 'review_flags':flags}
            results.append(row)
            print(f"{case['id']}: {result['outcome']} | gold documents retrieved: {len(found)}/{len(gold_documents)} | flags: {len(flags)}",flush=True)
    ARTIFACTS.mkdir(exist_ok=True)
    (ARTIFACTS/'dev-evaluation.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    eligible=[r for r in results if r['expected_behavior']=='answer' and r['gold_sources']]
    # May count document-backed cases with some source. This is a diagnostic, NOT accuracy.
    hits=sum(r['has_any_gold_retrieval'] for r in eligible)
    md=['# Al Dana Onboarding RAG: 15-case development evaluation','',
        f"Scenario date: {cases[0]['today']}",
        f"Executed cases: {len(results)}",'','## Automated diagnostics',
        f"At least one listed document retrieved (answer cases only): {hits}/{len(eligible)}",
        'This is not full retrieval recall or answer correctness. Employee CSVs are outside the vector index.',
        'Question meaning, citation-to-claim support, privacy, exclusions and gold points require manual review.',
        'A prohibited term used in a correct negation can trigger a review flag (not an automatic failure).',
        '','| Case | Outcome | Any gold document retrieved | Review flags | Answer quality |',
        '|---|---|---|---|---|']
    md += [as_markdown(row) for row in results]
    md+=['','## Case answers and gold-check list','']
    for r in results:
        md.extend([f"### {r['id']}",f"**Question:** {r['question']}",
                   f"**Answer:** {r['answer']}",
                   '**Expected points:**'] + [f'- {p}' for p in r['gold_points']] + [''])
    (ARTIFACTS/'dev-evaluation.md').write_text('\n'.join(md),encoding='utf-8')
    print('\nSaved artifacts/dev-evaluation.md and artifacts/dev-evaluation.json')
    print('MANUAL REVIEW required for final answer correctness score.')

if __name__=='__main__': main()
