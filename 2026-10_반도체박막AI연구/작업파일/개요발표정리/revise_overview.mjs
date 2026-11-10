import fs from 'node:fs/promises';
import crypto from 'node:crypto';
import {FileBlob,PresentationFile} from 'file:///C:/Users/박영우/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs';
import {finalizePresentation} from 'file:///C:/Users/박영우/.codex/plugins/cache/openai-primary-runtime/presentations/26.1025.11240/skills/presentations/container_tools/artifact_tool_utils.mjs';
const root='C:/Users/박영우/Documents/심부름/2026-10_반도체박막AI연구';
const build=root+'/작업파일/개요발표정리';
const source=root+'/최종/CUAI_반도체박막_주제발표.pptx';
const skill='C:/Users/박영우/.codex/plugins/cache/openai-primary-runtime/presentations/26.1025.11240/skills/presentations';
const p=await PresentationFile.importPptx(await FileBlob.load(source));
const records=(await p.inspect({kind:'textbox,shape',maxChars:1000000})).ndjson.split('\n').filter(Boolean).map(x=>JSON.parse(x));
function change(i,start,value,opt={}){
 const r=records.find(x=>x.kind==='textbox'&&x.slideIndex===i&&x.text.startsWith(start));
 if(!r)throw new Error('Missing text '+i+' '+start);
 const sh=p.resolve(r.id);sh.text=value.split('\n').map(x=>({runs:[x],spaceBefore:0,spaceAfter:0}));
 sh.text.style={typeface:'Malgun Gothic',fontSize:opt.size??r.style.fontSize,bold:r.style.bold??false,color:r.style.color??'#19264B',alignment:r.style.alignment??'left',verticalAlignment:opt.vertical??((r.fillColor||r.lineColor)?'middle':'top'),insets:(r.fillColor||r.lineColor)?6:0,wrap:'square',autoFit:'none'};
 if(opt.frame)sh.position={...r.position,...opt.frame};return sh;
}
change(2,'MLP 회귀 모델','MLP 한 종류 학습\n원본 데이터 기준');
change(2,'안정성 비교','예측 결과 비교');
change(2,'MAE·MAPE 변화','전체·층별 예측 오차\n원본 대비 예측 변화');
change(3,'입력만 바꾸고','같은 박막인데 반사율이 달라지면,\nAI의 두께 예측은 얼마나 흔들릴까?',{size:22,frame:{top:100,height:65}});
change(3,'MAE · 절대오차','예측 정확도와 예측의 흔들림을 함께 확인');
change(3,'잡음 수준에 따른','같은 정답을 기준으로 원본과 잡음 추가 예측을 전체·층별로 비교');
change(4,'분석 목표와 선택 확장','층별 비교와 해석 방향');
change(4,'기본 목표 · 모델이','잡음에 따른 정확도 저하와 층별 차이 확인');
change(4,'잡음 수준별 MAE','전체 예측 정확도\n네 층의 예측 변화');
change(4,'예측 안정성','민감한 층과\n조건 확인');
change(4,'선택 확장 · 시간이','재료·적층 위치 관점에서 결과 해석');
change(4,'원본으로 학습한','질화규소\n1층과 3층');
change(4,'잡음을 추가해 학습한','이산화규소\n2층과 4층');
change(4,'동일 조건에서 비교','같은 재료,\n다른 위치',{frame:{top:397,height:59}});
change(4,'원본 정확도와','선택 확장 · 여유가 있으면 잡음 증강 학습 비교');
for(const r of records.filter(x=>x.kind==='shape'&&x.slideIndex===4&&x.geometry==='straightConnector1'&&x.position.top>380&&x.position.left>125))p.delete(r.id);
const noteSources=[
 '이미지 출처: https://dacon.s3.ap-northeast-2.amazonaws.com/competition/235554/header_background.jpeg\n대회: https://dacon.io/competitions/official/235554/data',
 '데이터·구조: https://dacon.io/competitions/official/235554/data\n반사율 그림: dodo, 2020-01-28, https://dacon.io/competitions/official/235554/talkboard/400210\n생성 조건: https://dacon.io/competitions/official/235554/talkboard/400310',
 '',
 '원본 생성 조건: https://dacon.io/competitions/official/235554/talkboard/400310',
 '적층 구조: https://dacon.io/competitions/official/235554/data',
 ''
];
for(const [i,s] of p.slides.items.entries())s.speakerNotes.text=noteSources[i];
await fs.mkdir(build+'/검증완료',{recursive:true});await fs.mkdir(build+'/검수',{recursive:true});
await (await PresentationFile.exportPptx(p)).save(build+'/candidate.pptx');
const result=await finalizePresentation({workspaceDir:root,candidatePath:build+'/candidate.pptx',finalPath:build+'/검증완료/CUAI_반도체박막_주제발표.pptx',
 pythonExecutable:'C:/Users/박영우/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe',
 integrityValidatorPath:skill+'/container_tools/inspect_presentation_package_integrity.py',layoutValidatorPath:skill+'/container_tools/inspect_presentation_layout_geometry.py',
 layoutArgs:['--expected-slide-size-emu','9144000,5143500','--validate-heading-fit','--require-native-table-slide','2'],
 explicitTotalSlideCount:6,requiredNativeTableOwnerSlides:[2],
 fontPolicy:{basis:'reference',families:['Malgun Gothic'],referencePath:source,referenceSha256:crypto.createHash('sha256').update(await fs.readFile(source)).digest('hex')},
 verifyArtifactToolImport:true,receiptPath:build+'/최종검증.json'});
const final=await PresentationFile.importPptx(await FileBlob.load(result.finalPath));
for(const [i,s] of final.slides.items.entries()){
 const png=await final.export({slide:s,format:'png',scale:1.3});
 await fs.writeFile(build+'/검수/slide-'+(i+1)+'.png',new Uint8Array(await png.arrayBuffer()));
}
await fs.writeFile(build+'/본문대조.ndjson',(await final.inspect({kind:'slide,textbox,image,table,notes',maxChars:1000000})).ndjson);
console.log(JSON.stringify({file:result.finalPath,slides:final.slides.items.length,bytes:result.byteCount}));
