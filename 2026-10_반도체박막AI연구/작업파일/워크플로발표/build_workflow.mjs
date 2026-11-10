import fs from 'node:fs/promises';
import crypto from 'node:crypto';
import {FileBlob,PresentationFile} from 'file:///C:/Users/박영우/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs';
import {finalizePresentation} from 'file:///C:/Users/박영우/.codex/plugins/cache/openai-primary-runtime/presentations/26.1025.11240/skills/presentations/container_tools/artifact_tool_utils.mjs';

const root='C:/Users/박영우/Documents/심부름/2026-10_반도체박막AI연구';
const build=root+'/작업파일/워크플로발표';
const source=root+'/최종/CUAI_반도체박막_주제발표.pptx';
const skill='C:/Users/박영우/.codex/plugins/cache/openai-primary-runtime/presentations/26.1025.11240/skills/presentations';
const p=await PresentationFile.importPptx(await FileBlob.load(source));
const navy='#19264B',blue='#3875D1',gray='#526174',pale='#EDF3FA',font='Malgun Gothic';
function text(slide,value,x,y,w,h,size=22,{bold=false,color=navy,align='left'}={}){
 const s=slide.shapes.add({geometry:'textbox',name:value.slice(0,40),position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
 s.text=value.split('\n').map(v=>({runs:[v],spaceBefore:0,spaceAfter:0}));
 s.text.style={typeface:font,fontSize:size,bold,color,alignment:align,verticalAlignment:'top',wrap:'square',autoFit:'none',insets:0};return s;
}
function node(slide,value,x,y,w,h,{size=21,fill=pale,color=navy,border='#C8D4E3'}={}){
 const s=slide.shapes.add({geometry:'rect',name:value.replaceAll('\n',' '),position:{left:x,top:y,width:w,height:h},fill,line:{fill:border,width:1}});
 s.text=value.split('\n').map(v=>({runs:[v],spaceBefore:0,spaceAfter:0}));
 s.text.style={typeface:font,fontSize:size,color,bold:true,alignment:'center',verticalAlignment:'middle',insets:6,wrap:'square',autoFit:'none'};return s;
}
function connect(slide,a,b,{color=blue,kind='straight',from='right',to='left',dash=false}={}){
 return slide.shapes.connect(a,b,{kind,fromSide:from,toSide:to,line:{fill:color,width:2,style:dash?'dashed':'solid'},tail:{type:'triangle',width:'med',length:'med'}});
}
function head(s,str){text(s,str,148,32,770,52,28,{bold:true});}
// Keep the reference's left CUAI logo, navy band and closing slide.
for(let i=0;i<5;i++){
 const s=p.slides.items[i];
 for(const sh of [...s.shapes.items])if(sh.position.left>125)sh.delete();
 for(const im of [...s.images.items])if(im.position.left>125)im.delete();
}

const s0=p.slides.items[0];
s0.images.add({blob:new Uint8Array(await fs.readFile(build+'/assets/dacon_official_banner.jpeg')),contentType:'image/jpeg',alt:'DACON 반도체 박막 두께 분석 경진대회 공식 배너 사진',position:{left:148,top:92,width:760,height:145},fit:'contain'});
text(s0,'반도체 박막 두께 예측 AI\n잡음 안정성 평가',148,278,760,112,34,{bold:true});
text(s0,'CUAI 프로젝트 주제 발표',148,415,740,34,22);
text(s0,'실험 전 연구 계획   2026.10',148,461,740,30,18,{color:gray});

const s1=p.slides.items[1];head(s1,'반사율 데이터와 예측 대상');
text(s1,'반사율 패턴에서 네 개 박막층의 두께를 추정',160,108,750,36,23,{bold:true});
text(s1,'입력 · 226개 채널의 반사율',160,168,450,32,21,{bold:true});
s1.images.add({blob:new Uint8Array(await fs.readFile(build+'/assets/dacon_400210_0.png')),contentType:'image/png',alt:'DACON dodo 게시글에 공개된 네 층 두께 (10,10,10,10)의 반사율 스펙트럼 예시. x축 bb는 채널 번호, y축 aa는 반사율. 우리 팀 모델의 실험 결과가 아님.',position:{left:153,top:211,width:448,height:235},fit:'contain'});
text(s1,'출력 · 층별 두께 4개',655,168,255,32,21,{bold:true});
const layerValues=[['1층','질화규소','d₁'],['2층','이산화규소','d₂'],['3층','질화규소','d₃'],['4층','이산화규소','d₄'],['기판','규소','예측 제외']];
const t=s1.tables.add({rows:5,columns:3,left:650,top:214,width:270,height:215,columnWidths:[65,115,90],values:layerValues});
t.styleOptions={headerRow:false};t.borders.assign({fill:'#FFFFFF',width:2,style:'solid'});
for(let r=0;r<5;r++)for(let c=0;c<3;c++){
 const cell=t.getCell(r,c);cell.fill=r===4?navy:(r%2===0?'#DCE8F5':'#EDF2F8');
 cell.text.style={typeface:font,fontSize:16,bold:c===2,color:r===4?'#FFFFFF':navy,alignment:'center',verticalAlignment:'middle'};
}
// A native arrow connects the actual input figure and the layer output table.
s1.shapes.add({geometry:'connector',kind:'straight',position:{left:606,top:321,width:38,height:0},line:{fill:blue,width:2},tail:{type:'triangle'}});
text(s1,'학습 표본 약 81만 개 · 광학 계산 기반 합성 데이터',160,462,750,31,20);
text(s1,'그림: DACON dodo 공개 분석(2020) · 데이터 예시, 팀 실험 결과 아님',160,505,750,22,12.5,{color:gray});

const s2=p.slides.items[2];head(s2,'프로젝트 진행 흐름');
text(s2,'데이터를 준비하고, 모델을 만든 뒤 잡음의 영향을 비교',160,108,750,36,23,{bold:true});
const titles=['데이터 준비','기준 모델 학습','추가 잡음 주입','안정성 비교'];
const desc=['학습·검증 분리\n입력·정답 확인','MLP 회귀 모델\nMAE 손실 + Adam','같은 반사율 입력에\nGaussian Noise 추가','MAE·MAPE 변화\n층별·두께별 비교'];
const steps=[];
for(let i=0;i<4;i++){
 const x=160+i*190;
 const circle=s2.shapes.add({geometry:'ellipse',name:'워크플로 단계 '+(i+1),position:{left:x+57,top:207,width:56,height:56},fill:navy,line:{width:0,fill:'none'}});
 circle.text=String(i+1).padStart(2,'0');circle.text.style={typeface:font,fontSize:23,bold:true,color:'#FFFFFF',alignment:'center',verticalAlignment:'middle',insets:0};steps.push(circle);
 text(s2,titles[i],x,289,170,35,22,{bold:true,align:'center'});
 text(s2,desc[i],x-2,343,174,66,18,{color:gray,align:'center'});
}
for(let i=0;i<3;i++)connect(s2,steps[i],steps[i+1]);
text(s2,'현재는 주제·계획 수립 단계이며, 학습과 성능 시험은 앞으로 진행',160,465,750,40,19,{color:gray});

const s3=p.slides.items[3];head(s3,'잡음 전후 비교 계획');
text(s3,'입력만 바꾸고 동일한 학습 모델로 예측',160,108,750,36,23,{bold:true});
const input=node(s3,'같은 평가 표본\n같은 두께 정답',160,226,150,91,{size:20,fill:'#FFFFFF'});
const original=node(s3,'원본 입력',366,178,145,60);
const noisy=node(s3,'추가 잡음 입력',366,321,145,60);
const model1=node(s3,'학습된 MLP',558,178,145,60);
const model2=node(s3,'같은 MLP',558,321,145,60);
const out1=node(s3,'원본 예측',750,178,150,60,{fill:'#FFFFFF'});
const out2=node(s3,'잡음 추가 예측',750,321,150,60,{fill:'#FFFFFF'});
connect(s3,input,original,{kind:'elbow'});connect(s3,input,noisy,{kind:'elbow'});
connect(s3,original,model1);connect(s3,noisy,model2);connect(s3,model1,out1);connect(s3,model2,out2);
text(s3,'Gaussian Noise',366,391,150,24,15,{color:gray,align:'center'});
text(s3,'MAE · 절대오차     MAPE · 상대오차',160,446,750,36,24,{bold:true});
text(s3,'잡음 수준에 따른 오차 증가와 예측 변화량을 층별·두께 구간별로 비교',160,494,750,28,17,{color:gray});

const s4=p.slides.items[4];head(s4,'분석 목표와 선택 확장');
text(s4,'기본 목표 · 모델이 취약한 조건 정리',160,108,750,35,23,{bold:true});
const analysis=node(s4,'잡음 수준별 MAE·MAPE\n층별·두께 구간별 차이',160,175,420,96,{size:24,fill:'#FFFFFF'});
const conclusion=node(s4,'예측 안정성\n해석·정리',699,175,200,96,{size:24});connect(s4,analysis,conclusion);
text(s4,'선택 확장 · 시간이 된다면 잡음 증강 학습 적용',160,326,750,35,22,{bold:true});
const b0=node(s4,'원본으로 학습한\n기준 모델',160,389,235,80,{size:21,fill:'#FFFFFF'});
const b1=node(s4,'잡음을 추가해 학습한\n증강 모델',665,389,235,80,{size:21,fill:'#FFFFFF'});
s4.shapes.connect(b0,b1,{kind:'straight',fromSide:'right',toSide:'left',line:{fill:blue,width:2,style:'dashed'},head:{type:'triangle'},tail:{type:'triangle'}});
text(s4,'동일 조건에서 비교',425,379,210,31,20,{align:'center'});
text(s4,'원본 정확도와 잡음 조건의 성능을 함께 확인',160,498,750,28,18,{color:gray});

const data='https://dacon.io/competitions/official/235554/data';
const post='https://dacon.io/competitions/official/235554/talkboard/400210';
const generation='https://dacon.io/competitions/official/235554/talkboard/400310';
const banner='https://dacon.s3.ap-northeast-2.amazonaws.com/competition/235554/header_background.jpeg';
const notes=[
 '반도체·소재 전공과 AI 회귀 모델을 연결해, 추가 입력 잡음이 박막 두께 예측에 미치는 영향을 평가할 계획입니다. 현재는 주제와 워크플로를 정한 단계이며 모델 학습·성능 시험은 진행하지 않았습니다.\n표지 이미지: DACON 공식 대회 배너 원본 '+banner+'\n대회 소개: '+data,
 '입력226개 반사율 값에서 질화규소/이산화규소/질화규소/이산화규소4층 두께를 추정합니다. 기판은 예측 대상에서 제외합니다. 학습표본810000개라는 수치는 원본 전수 확인 결과입니다. 표는 적층 순서만 보여주며 실제 두께 비례 그림이 아닙니다. 공개 반사율 그림은 dodo가2020-01-28 올린 (10,10,10,10) 조합 예시입니다. aa=반사율, bb=채널번호. 이 그림은 우리 팀이 실시한 모델 실험 결과가 아닙니다. 두께 물리단위는 아직 확인 전이며 nm로 단정하지 않습니다.\n데이터 설명: '+data+'\n그림: '+post+'\n합성+약1%기존잡음: '+generation,
 '주제발표에서는 전체 워크플로만 설명합니다. 데이터 분할과 전처리를 고정하고 MLP 다중 출력 회귀 모델을 학습합니다. MAE 손실과 Adam을 사용하며 구체적 파라미터는 예비 실행 후 정합니다. 최종 평가 자료는 모델 선택에 사용하지 않습니다. 이후 같은 표본에 추가 가우시안 잡음을 주어 정확도와 예측 일관성을 함께 비교하려 합니다. 현재 모델 성능 결과는 없습니다.',
 '두 경로는 동일한 평가 표본과 동일한 학습 모델의 가중치를 사용합니다. 모델을 매 잡음 조건마다 새로 학습하는 것이 아닙니다. 원본에도 생성 시 잡음이 포함되어 있으므로 원본 경로를 무잡음으로 부르지 않습니다. 추가 잡음은 원래 반사율 스케일에서 더하고 학습 자료로 구한 고정 표준화를 적용합니다. MAE는 원본 두께 값의 절대오차, MAPE는 표본별 정답 두께 대비 상대오차이며 %로 표기합니다. 두 지표를 함께 보고 층별·두께 구간별 차이와 원본 예측 대비 변화량을 평가할 계획입니다. 얇은 구간의 큰 MAPE만으로 잡음 민감도를 단정하지 않습니다.\nMAPE 정의: https://scikit-learn.org/stable/modules/generated/sklearn.metrics.mean_absolute_percentage_error.html\n기존 잡음: '+generation,
 '기본 목표는 모델 구현과 잡음 조건별 정확도·일관성 분석입니다. 결과를 보고 취약한 층이나 두께 구간을 정리하려 합니다. 시간이 되면 학습 입력에 잡음을 더하는 Noise Augmentation 모델을 만들고 같은 조건에서 기준 모델과 비교합니다. 원본 정확도의 손실도 함께 살펴보며 개선을 미리 약속하지 않습니다. 이 연구는 합성 데이터에서의 모델 민감도이며 실제 장비의 허용오차나 재료 고유 민감도를 직접 검증하는 실험은 아닙니다.',
 '감사합니다. 연구 주제와 진행 계획에 대한 의견을 부탁드립니다.'
];
for(const [i,s] of p.slides.items.entries())s.speakerNotes.text=notes[i];
await fs.mkdir(build+'/검수',{recursive:true});await fs.mkdir(build+'/검증완료',{recursive:true});
await (await PresentationFile.exportPptx(p)).save(build+'/candidate.pptx');
const r=await finalizePresentation({workspaceDir:root,candidatePath:build+'/candidate.pptx',finalPath:build+'/검증완료/이미지포함검수본.pptx',
 pythonExecutable:'C:/Users/박영우/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe',
 integrityValidatorPath:skill+'/container_tools/inspect_presentation_package_integrity.py',layoutValidatorPath:skill+'/container_tools/inspect_presentation_layout_geometry.py',
 layoutArgs:['--expected-slide-size-emu','9144000,5143500','--validate-bullet-geometry','--validate-heading-fit','--require-native-table-slide','2'],
 explicitTotalSlideCount:6,requiredNativeTableOwnerSlides:[2],
 fontPolicy:{basis:'reference',families:[font],referencePath:source,referenceSha256:crypto.createHash('sha256').update(await fs.readFile(source)).digest('hex')},
 verifyArtifactToolImport:true,receiptPath:build+'/이미지포함검증.json'});
const final=await PresentationFile.importPptx(await FileBlob.load(r.finalPath));
for(const [i,s] of final.slides.items.entries()){
 const png=await final.export({slide:s,format:'png',scale:1.3});
 await fs.writeFile(build+'/검수/slide-'+(i+1)+'.png',new Uint8Array(await png.arrayBuffer()));
}
await fs.writeFile(build+'/content.inspect.ndjson',(await final.inspect({kind:'slide,textbox,table,image,shape',maxChars:1000000})).ndjson);
console.log(JSON.stringify({file:r.finalPath,slides:final.slides.items.length,bytes:r.byteCount}));
