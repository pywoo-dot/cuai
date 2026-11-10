import fs from 'node:fs/promises';
import crypto from 'node:crypto';
import {FileBlob,PresentationFile} from 'file:///C:/Users/박영우/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs';
import {finalizePresentation} from 'file:///C:/Users/박영우/.codex/plugins/cache/openai-primary-runtime/presentations/26.1025.11240/skills/presentations/container_tools/artifact_tool_utils.mjs';
const root='C:/Users/박영우/Documents/심부름/2026-10_반도체박막AI연구';
const build=root+'/작업파일/피드백지표추가';
const source=root+'/최종/CUAI_반도체박막_주제발표_개요.pptx';
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
change(3,'같은 정답을 기준으로','전체·층별 오차는 MAE(절대오차)와 MAPE(상대오차)로 비교');
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

