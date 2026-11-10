import fs from 'node:fs/promises';
import crypto from 'node:crypto';
import {FileBlob,PresentationFile} from 'file:///C:/Users/박영우/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs';
import {makeNativeBulletParagraphs,finalizePresentation} from 'file:///C:/Users/박영우/.codex/plugins/cache/openai-primary-runtime/presentations/26.1024.11018/skills/presentations/container_tools/artifact_tool_utils.mjs';

const root='C:/Users/박영우/Documents/심부름/2026-10_반도체박막AI연구';
const build=root+'/작업파일/주제발표간소화';
const skill='C:/Users/박영우/.codex/plugins/cache/openai-primary-runtime/presentations/26.1024.11018/skills/presentations';
const ref='C:/Users/박영우/Documents/카카오톡 받은 파일/BASIC_2조_발표자료.pptx';
const fontSource='C:/Users/박영우/Documents/카카오톡 받은 파일/cuai 중간 발표 _2026.2.pptx';
const p=await PresentationFile.importPptx(await FileBlob.load(ref));
// Reference cover, four subject slides, and closing. Remove study photo and TOC.
p.slides.keep([0,3,4,5,6,7]);
const rec=(await p.inspect({kind:'textbox,image',maxChars:1000000})).ndjson.split('\n').filter(Boolean).map(x=>JSON.parse(x));
const textRecords=rec.filter(x=>x.kind==='textbox');
const navy='#19264B',font='Malgun Gothic';
function assign(sh,value,{size=26.67,bold=false,color='#111111',alignment='left'}={}){
 sh.text=value;
 sh.text.style={typeface:font,fontSize:size,bold,color,alignment,verticalAlignment:'top',insets:0,wrap:'square',autoFit:'none'};
}
function box(slide,value,x,y,w,h,opts={}){
 const sh=slide.shapes.add({geometry:'textbox',name:value.slice(0,35),position:{left:x,top:y,width:w,height:h},fill:'none',line:{width:0,fill:'none'}});
 assign(sh,value,opts);return sh;
}
// Preserve the CUAI logo images; remove unrelated medical/Kaggle images.
for(const r of rec.filter(x=>x.kind==='image'&&x.position.left>125))p.delete(r.id);

const cover=p.slides.items[0];
for(const r of textRecords.filter(x=>x.slideIndex===0))p.delete(r.id);
box(cover,'반도체 박막 두께 예측 AI\n잡음 안정성 평가',148,190,750,115,{size:34,bold:true,color:navy});
box(cover,'CUAI 프로젝트 주제 발표',148,338,740,42,{size:22,color:navy});
box(cover,'실험 전 연구 계획   2026.10',148,395,740,35,{size:18,color:navy});

const titles=['주제 선정','데이터셋 소개','진행 계획','프로젝트 목표'];
const items=[
 ['반도체·소재 분야의 전공 지식을\n활용할 수 있는 프로젝트',
  '공개 데이터로 다중 출력 회귀 모델을\n구현하며 머신러닝 분석 과정을 학습',
  '입력 반사율에 잡음이 더해졌을 때\n두께 예측이 얼마나 달라지는지 확인'],
 ['데이콘 반도체 박막 두께 데이터 활용\n정답이 있는 학습 표본 약 81만 개',
  '입력은 226개 채널의 반사율,\n출력은 4개 박막층의 두께',
  '광학 계산에 잡음을 더한 합성 데이터\n각 층의 두께는 10~300 범위'],
 ['MLP 회귀 모델로 4개 층의 두께 예측\n학습에는 MAE와 Adam 사용',
  '반사율에 Gaussian Noise를 추가하고\n잡음 수준에 따른 예측 오차 비교',
  'MAE와 MAPE를 함께 확인하고\n층별·두께 구간별 차이를 분석'],
 ['반사율로 박막 두께를 예측하는\n기본 회귀 모델 구현',
  '추가 잡음이 예측에 미치는 영향을\n절대오차와 상대오차로 정리',
  '시간이 된다면 잡음 증강 학습을 적용해\n기존 모델과 안정성 비교']
];
for(let i=1;i<=4;i++){
 const records=textRecords.filter(x=>x.slideIndex===i);
 const head=records.find(x=>x.position.top<90);
 const body=records.find(x=>x.position.top>100);
 const hs=p.resolve(head.id);assign(hs,titles[i-1],{size:28,bold:true,color:navy});
 hs.position={left:148,top:32,width:735,height:56};
 const bs=p.resolve(body.id);
 const bullets=makeNativeBulletParagraphs(items[i-1],{marginLeftPoints:19,hangingPoints:12,spaceAfterPoints:24});
 assign(bs,bullets,{size:26.67});
 bs.position={left:211,top:137,width:700,height:352};
}
const endRecord=textRecords.find(x=>x.slideIndex===5);
assign(p.resolve(endRecord.id),'감사합니다',{size:64,color:'#FFFFFF',alignment:'center'});

const dataSource='https://dacon.io/competitions/official/235554/data';
const generation='https://dacon.io/competitions/official/235554/talkboard/400310';
const metricSource='https://scikit-learn.org/stable/modules/generated/sklearn.metrics.mean_absolute_percentage_error.html';
const notes=[
 '반도체 박막 두께 예측 AI의 잡음 안정성 평가를 진행할 계획입니다. 현재는 주제와 진행 방향을 정한 단계이며, 모델 학습이나 성능 시험은 아직 하지 않았습니다.',
 '팀원들의 반도체·소재 관심과 전공 지식을 활용하고, 회귀 모델 구축과 평가를 경험할 수 있는 주제를 선정했습니다. 특히 입력 반사율이 조금 변했을 때 예측 두께가 얼마나 달라지는지 확인하려 합니다. 층별 취약성이나 개선 효과는 앞으로 확인할 내용입니다.',
 '데이콘 공개 학습 데이터는 약81만 표본이며 입력226개 반사율과 출력4개 두께로 구성됩니다. 공식 설명은 계산된 반사율에 약1% 잡음을 추가한 합성 데이터임을 밝힙니다. 각 층의 두께 범위는 기존 원본 전수 분석에서10~300으로 확인했습니다. 단위 확인 전에는 nm로 표기하지 않습니다.\n데이터: '+dataSource+'\n생성 조건: '+generation,
 '우선 MLP 다중 출력 회귀 모델을 학습하고 반사율에 추가 정규 잡음을 주어 오차를 비교할 계획입니다. MAE는 절대오차, MAPE는 정답 두께 대비 상대오차입니다. 팀원 피드백을 반영해 두 지표를 함께 보려 합니다. 잡음 세기와 세부 학습값은 예비 실행 후 결정합니다. 원본에도 잡음이 있으므로 추가 잡음 없는 원본을 기준으로 비교합니다. 학습·검증·평가 자료는 분리합니다.\nMAPE 정의: '+metricSource,
 '기본 모델 구현과 추가 잡음의 영향 정리가 우선 목표입니다. 여유가 있으면 학습 입력에도 잡음을 더하는 잡음 증강을 적용해 비교하려 합니다. 개선 여부는 실험 후 판단합니다. 현재는 성능 결과가 없습니다.',
 '감사합니다. 연구 주제와 진행 계획에 대한 의견을 부탁드립니다.'
];
for(const [i,s] of p.slides.items.entries())s.speakerNotes.text=notes[i];
await fs.mkdir(build+'/검수',{recursive:true});
await (await PresentationFile.exportPptx(p)).save(build+'/candidate.pptx');
await fs.writeFile(build+'/content.inspect.ndjson',(await p.inspect({kind:'slide,textbox,image,notes',maxChars:1000000})).ndjson);
const result=await finalizePresentation({
 workspaceDir:root,candidatePath:build+'/candidate.pptx',finalPath:root+'/최종/CUAI_반도체박막_주제발표.pptx',
 pythonExecutable:'C:/Users/박영우/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe',
 integrityValidatorPath:skill+'/container_tools/inspect_presentation_package_integrity.py',
 layoutValidatorPath:skill+'/container_tools/inspect_presentation_layout_geometry.py',
 layoutArgs:['--expected-slide-size-emu','9144000,5143500','--validate-bullet-geometry','--validate-heading-fit'],
 explicitTotalSlideCount:6,
 fontPolicy:{basis:'reference',families:[font],referencePath:fontSource,referenceSha256:crypto.createHash('sha256').update(await fs.readFile(fontSource)).digest('hex')},
 verifyArtifactToolImport:true,receiptPath:build+'/최종검증.json'
});
// Render the delivered file, rather than only the in-memory pre-export deck.
const final=await PresentationFile.importPptx(await FileBlob.load(result.finalPath));
for(const [i,s] of final.slides.items.entries()){
 const png=await final.export({slide:s,format:'png',scale:1.3});
 await fs.writeFile(build+'/검수/slide-'+(i+1)+'.png',new Uint8Array(await png.arrayBuffer()));
}
console.log(JSON.stringify({finalPath:result.finalPath,slides:final.slides.items.length,bytes:result.byteCount}));
