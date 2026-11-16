"use strict";
const $ = id => document.getElementById(id);
const state = {crops: [], analysis: null, selectedDate: null};
const format = (value, digits=1) => value == null ? "Unavailable" : Number(value).toLocaleString("en-US", {minimumFractionDigits:digits, maximumFractionDigits:digits});
const escapeHtml = text => String(text ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
function message(text, error=false) {$("message").textContent=text; $("message").hidden=!text; $("message").classList.toggle("error",error);}
async function api(path, options={}) {const r=await fetch(path,options); const data=await r.json(); if(!r.ok) throw new Error(data.error?.message || "The request failed."); return data;}
function view(name) {document.querySelectorAll(".view").forEach(el=>el.hidden=el.id!==name);document.querySelectorAll(".nav-item").forEach(el=>el.classList.toggle("active",el.dataset.view===name));message("");}
document.querySelectorAll("[data-view]").forEach(el=>el.addEventListener("click",()=>view(el.dataset.view)));
$("open-planting").addEventListener("click",()=>view("planting"));
function chart(containerId, points, type="bar", mean=null) {
  const el=$(containerId); if(!points.length){el.innerHTML='<div class="chart-empty">No complete local data are available for this period.</div>';return;}
  const w=960,h=type==="bar"?270:210,l=43,r=16,t=12,b=35,plotW=w-l-r,plotH=h-t-b;
  const vals=points.flatMap(p=>[p.value,p.fitted].filter(v=>v!=null));
  const min=type==="bar"?0:Math.floor((Math.min(...vals)-.15)*2)/2;
  const max=type==="bar"?Math.ceil(Math.max(...vals)/200)*200:Math.ceil((Math.max(...vals)+.15)*2)/2;
  const y=v=>t+plotH-(v-min)/(max-min||1)*plotH;
  const x=i=>l+(i+.5)*plotW/points.length;
  let shapes="";
  for(let i=0;i<=4;i++){const v=min+(max-min)*i/4;shapes+=`<line x1="${l}" y1="${y(v)}" x2="${w-r}" y2="${y(v)}" stroke="#edf0e8"/><text x="${l-9}" y="${y(v)+3}" text-anchor="end">${format(v,type==="bar"?0:1)}</text>`;}
  points.forEach((p,i)=>{if(i%Math.max(1,Math.floor(points.length/9))===0||i===points.length-1)shapes+=`<text x="${x(i)}" y="${h-10}" text-anchor="middle">${p.year}</text>`;});
  if(type==="bar") {const bw=Math.max(2,plotW/points.length*.57);points.forEach((p,i)=>shapes+=`<rect x="${x(i)-bw/2}" y="${y(p.value)}" width="${bw}" height="${y(0)-y(p.value)}" rx="2" fill="${p.value<mean?'#b6c8a2':'#769765'}"><title>${p.year}: ${format(p.value)} mm</title></rect>`);}
  else {shapes+=`<polyline fill="none" stroke="#527b45" stroke-width="2" points="${points.map((p,i)=>`${x(i)},${y(p.value)}`).join(' ')}"/>`;points.forEach((p,i)=>shapes+=`<circle cx="${x(i)}" cy="${y(p.value)}" r="3" fill="#527b45"><title>${p.year}: ${format(p.value,2)} °C</title></circle>`);if(points[0].fitted!=null)shapes+=`<polyline fill="none" stroke="#c19a62" stroke-width="1.5" stroke-dasharray="5 4" points="${points.map((p,i)=>`${x(i)},${y(p.fitted)}`).join(' ')}"/>`;}
  if(mean!=null)shapes+=`<line x1="${l}" y1="${y(mean)}" x2="${w-r}" y2="${y(mean)}" stroke="#b47a43" stroke-dasharray="5 4"/>`;
  el.innerHTML=`<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="${type==='bar'?'Annual rainfall':'Annual mean temperature with Theil–Sen trend'}">${shapes}</svg>`;
}
async function loadOverview() {
  const start=Number($("start-year").value),end=Number($("end-year").value);
  if(start>end){message("The start year must not exceed the end year.",true);return;}
  message("Loading historical climate…");
  try{
    const result=await api(`/api/v1/climate/trends?municipality_id=2504009&start_year=${start}&end_year=${end}`);
    const rain=result.indicators.precipitation,temp=result.indicators.temperature_mean;
    $("rain-mean").innerHTML=rain.status==="available"?`${format(rain.mean,1)}<small>mm / year</small>`:"Unavailable";
    $("rain-range").textContent=rain.status==="available"?`${rain.complete_years} complete years · ${start}–${end}`:rain.reason;
    $("temp-mean").innerHTML=temp.status==="available"?`${format(temp.mean,2)}<small>°C</small>`:"Unavailable";
    $("temp-range").textContent=temp.status==="available"?`${temp.complete_years} complete years · Daily mean air temperature` : temp.reason;
    $("temp-trend").innerHTML=temp.status==="available"?`${temp.trend.slope_per_decade>=0?'+':''}${format(temp.trend.slope_per_decade,3)}<small>°C / decade</small>`:"Unavailable";
    $("trend-detail").textContent=temp.status==="available"?`95% CI ${format(temp.trend.confidence_interval_95.lower,3)} to ${format(temp.trend.confidence_interval_95.upper,3)}`:"Insufficient data";
    $("temp-inference").textContent=temp.status==="available"?`Mann–Kendall p = ${format(temp.significance.p_value,4)}. ${temp.autocorrelation.detected?"Residual autocorrelation detected; original inference requires adjustment.":"No residual autocorrelation detected at lags 1–3; independence is not proven."}`:"No annual trend available.";
    chart("rain-chart",rain.annual_series||[],"bar",rain.mean);
    chart("temp-chart",temp.annual_series||[],"line");
    message("");
  }catch(e){message(e.message,true);}
}
$("period-form").addEventListener("submit",e=>{e.preventDefault();loadOverview();});
function updateWindow(){
  const crop=state.crops.find(c=>c.id===Number($("crop").value));
  if(!crop)return;
  $("window-label").textContent=`Window: ${crop.window_start.replace('-','/')} — ${crop.window_end.replace('-','/')} · rainfed`;
  const required=[...new Set((crop.climate_checks||[]).filter(c=>c.include_in_assessment&&!c.optional_when_window_missing&&c.phase!=="cycle").map(c=>c.phase))];
  $("check-window-help").textContent=`Required for a combined percentage: ${required.join(', ')}. Supply inclusive day offsets below or as phase IDs. Set phase_id on a check window to link its results to a submitted phase card; the window must fit inside that phase. Add germination, grain_filling and maturation windows for all phase cards. Maturation must cover the final 10 cycle days. The whole-cycle window is automatic. No cultivar dates are assumed.`;
}
$("crop").addEventListener("change",updateWindow);
function renderSources(result){
  $("source-cards").innerHTML=Object.entries(result.variables).map(([variable,s])=>{
    const m=s.source;if(!m)return `<article class="panel source-card"><h2>${escapeHtml(variable)}</h2><p>No source imported.</p></article>`;
    const rows=[["Product",m.product],["Coverage",`${m.start_date} — ${m.end_date}`],["Actual grid coordinates",m.actual_bbox.join(', ')],["Original resolution",m.source_resolution],["Original / daily unit",`${m.source_unit} / ${m.daily_unit}`],["Raw / daily records",`${m.raw_record_count.toLocaleString('en-US')} / ${m.daily_record_count.toLocaleString('en-US')}`],["Missing timestamps",m.missing_timestamps],["Incomplete days",m.incomplete_days],["Input order",m.input_was_sorted?"Already chronological":"Sorted during import"],["Daily boundary",m.daily_boundary],["Method",m.aggregation_method],["SHA-256",m.sha256]];
    return `<article class="panel source-card"><div class="source-title"><h2>${variable==="precipitation"?"Precipitation":"Mean air temperature"}</h2><span class="status ${s.status==='available'?'':'unavailable'}">${s.status==='available'?'REGIONAL SOURCE VERIFIED':'SOURCE AREA MISMATCH'}</span></div><dl>${rows.map(([k,v])=>`<dt>${escapeHtml(k)}</dt><dd class="${k==='SHA-256'?'hash':''}">${escapeHtml(v)}</dd>`).join('')}</dl></article>`;
  }).join('');
}
function prettyDate(value){return new Date(value+'T12:00:00Z').toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric',timeZone:'UTC'});}
function metricMean(indicator,key){return indicator?.[key]?.mean ?? null;}
function scenarioCell(scenario){
  if(scenario?.status!=="available")return '<span title="Define all required phase windows and provide complete data">Unavailable</span>';
  return `${format(scenario.scenario_criteria_met_pct)}%<br><small>${scenario.years_meeting_criteria}/${scenario.evaluated_years} years</small><br><small>${escapeHtml(scenario.risk_level)} exposure</small>`;
}
function appendScenarioAssessment(scenario){
  const section=document.createElement("section");section.className="scenario-summary";
  if(scenario?.status!=="available"){
    const phases=[...new Set((scenario?.blocking_checks||[]).map(check=>check.phase))];
    section.innerHTML='<h2>Scenario criteria match</h2>';
    const note=document.createElement("p");note.className="small-note";
    note.textContent=`Unavailable: ${scenario?.reason||'not calculated in this saved analysis'}. `+
      (phases.length?`Check the required windows: ${phases.join(', ')}.`:'No common complete evaluation years may be available.');
    section.appendChild(note);
  }else{
    section.innerHTML=`<div class="eyebrow">HISTORICAL SCENARIO CRITERIA MATCH</div><div class="scenario-percentage">${format(scenario.scenario_criteria_met_pct)}%</div><p><strong>${escapeHtml(scenario.risk_level)} climate exposure</strong> · ${format(scenario.exposure_frequency_pct)}% of evaluated years had at least one configured event.</p><p>${scenario.years_meeting_criteria} of ${scenario.evaluated_years} complete historical years met every included criterion.</p><p class="small-note">${scenario.excluded_years.length} years excluded; ${scenario.omitted_optional_checks?.length||0} optional checks omitted because their windows were not supplied. This is not a probability of crop success, crop loss, or an official ZARC risk category.</p>`;
  }
  $("date-detail").appendChild(section);
}
function appendClimateChecks(checks){
  const section=document.createElement("section");
  section.innerHTML='<h2>Configured phase checks</h2><p class="small-note">Thermal checks use daily mean temperature, not daily maxima/minima. Frequencies describe years with the specified exposure, not crop-loss probability. Zero does not rule out daily extremes.</p>';
  for(const check of checks||[]){
    const row=document.createElement("p"); row.className="small-note";
    const title=`${check.definition.type} · ${check.phase} · ${check.variable}`;
    row.textContent=check.status!=="available"?`${title}: unavailable (${check.reason}).`:
      `${title}: mean ${format(check.summary.mean,2)} ${check.unit}; range ${format(check.summary.minimum,2)}–${format(check.summary.maximum,2)}. `+
      `${check.evaluated_years} complete years; ${check.excluded_years.length} excluded. `+
      (check.historical_event_frequency_pct==null?"Descriptive result; no event threshold defined.":
       `Years with the defined event: ${check.event_years}/${check.evaluated_years} (${format(check.historical_event_frequency_pct)}%).`);
    section.appendChild(row);
  }
  $("date-detail").appendChild(section);
}
function renderAnalysis(result){
  state.analysis=result;$("analysis-empty").hidden=true;$("analysis-result").hidden=false;
  const crop=state.crops.find(c=>c.id===result.crop_id);
  $("analysis-title").textContent=`${crop?.name||result.crop_id} · ${result.dates.length} planting dates`;
  $("analysis-meta").textContent=`${result.historical_period.start_year}–${result.historical_period.end_year} historical years · ${result.dates[0].cycle.duration_days}-day user scenario · user-supplied planting window`;
  $("date-results").innerHTML=result.dates.map(d=>{
    const a=d.historical_assessment;return `<tr data-date="${d.date}"><td><button data-date="${d.date}">${prettyDate(d.date)}</button></td><td>${scenarioCell(d.scenario_assessment)}</td><td>${format(metricMean(a.precipitation,'total_mm'),1)} ${a.precipitation.status==='available'?'mm':''}</td><td>${format(metricMean(a.temperature_mean,'mean_c'),2)} °C</td><td>${a.precipitation.evaluated_years} rain / ${a.temperature_mean.evaluated_years} temp</td></tr>`;
  }).join('');
  $("date-detail").replaceChildren();
  $("date-results").querySelectorAll("button").forEach(button=>button.addEventListener("click",()=>loadDate(button.dataset.date)));
}
async function loadDate(date){
  try{
    const r=await api(`/api/v1/planting/analyses/${state.analysis.analysis_id}/dates/${date}`);
    document.querySelectorAll("#date-results tr").forEach(el=>el.classList.toggle("selected",el.dataset.date===date));
    const a=r.historical_assessment;
    $("date-detail").innerHTML=`<h2>${prettyDate(date)}</h2><p class="small-note">Cycle ends ${prettyDate(r.cycle.estimated_last_cycle_date)}. All intervals are inclusive.</p><div class="detail-grid"><div class="detail-stat"><strong>${format(metricMean(a.precipitation,'total_mm'))} mm</strong><small>Mean cycle rainfall</small></div><div class="detail-stat"><strong>${format(metricMean(a.temperature_mean,'mean_c'),2)} °C</strong><small>Mean cycle temperature</small></div><div class="detail-stat"><strong>${format(metricMean(a.precipitation,'longest_dry_spell_days'))}</strong><small>Mean longest dry spell · days &lt; 1 mm</small></div></div><p class="small-note">Rainfall P10–P90: ${format(a.precipitation.total_mm?.p10)}–${format(a.precipitation.total_mm?.p90)} mm across historical cycles. These are observed distribution quantiles, not confidence limits.</p><p class="small-note">${r.phases.length?r.phases.map(p=>`${escapeHtml(p.name)} (days ${p.start_day}–${p.end_day}): ${escapeHtml(p.risk_level)} exposure · ${format(p.scenario_assessment?.exposure_frequency_pct)}% · ${format(metricMean(p.assessment.precipitation,'total_mm'))} mm, ${format(metricMean(p.assessment.temperature_mean,'mean_c'),2)} °C`).join('<br>'):'No phase definitions supplied. Crop risk and favorable frequency are unavailable without a validated agronomic profile.'}</p>`;
    appendScenarioAssessment(r.scenario_assessment);
    appendClimateChecks(r.climate_checks);
  }catch(e){message(e.message,true);}
}
$("planting-form").addEventListener("submit",async e=>{
  e.preventDefault();const button=$("run-analysis");button.disabled=true;message("Evaluating historical cycles…");
  try{
    const phases=$("phases").value.trim()?JSON.parse($("phases").value):[];
    const check_windows=$("check-windows").value.trim()?JSON.parse($("check-windows").value):[];
    const threshold=$("temp-threshold").value;
    const payload={municipality_id:2504009,crop_id:Number($("crop").value),production_system:"rainfed",planting_year:Number($("planting-year").value),cycle_days:Number($("cycle-days").value),historical_period:{start_year:Number($("history-start").value),end_year:Number($("history-end").value)},phases,check_windows,daily_mean_threshold_c:threshold===""?null:Number(threshold)};
    let r=await api("/api/v1/planting/analyses",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)});
    for(let attempt=0;attempt<300;attempt++){
      const result=await api(r.links.result);
      if(result.status==="completed"){renderAnalysis(result);message("Historical exposure is ready. Select a date for details.");return;}
      if(result.status==="failed")throw new Error(result.error?.message||"Analysis failed.");
      message(`Evaluating historical cycles… ${Math.round((result.progress||0)*100)}%`);
      await new Promise(resolve=>setTimeout(resolve,500));
    }
    throw new Error(`Processing is taking longer than expected. Check ${r.links.result}.`);
  }catch(error){message(error instanceof SyntaxError?"Phase definitions and check windows must be valid JSON arrays.":error.message,true);}finally{button.disabled=false;}
});
$("download-analysis").addEventListener("click",()=>{if(!state.analysis)return;const blob=new Blob([JSON.stringify(state.analysis,null,2)],{type:"application/json"});const url=URL.createObjectURL(blob);const a=document.createElement("a");a.href=url;a.download=`${state.analysis.analysis_id}.json`;a.click();URL.revokeObjectURL(url);});
async function init(){try{const [crops,sources]=await Promise.all([api("/api/v1/crops"),api("/api/v1/data/status")]);state.crops=crops.data;$("crop").replaceChildren(...crops.data.map(c=>{const o=document.createElement("option");o.value=c.id;o.textContent=c.name;return o;}));updateWindow();renderSources(sources);await loadOverview();}catch(e){message(e.message,true);}}
init();
