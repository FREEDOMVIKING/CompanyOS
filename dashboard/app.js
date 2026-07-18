function money(value){
  return new Intl.NumberFormat(
    "en-US",
    {style:"currency",currency:"USD"}
  ).format(Number(value||0));
}

function item(title,detail,extra=""){
  return `<div class="item"><strong>${title}</strong><br>`+
         `<small>${detail}</small>${extra}</div>`;
}

async function load(){
  const response=await fetch("/api/snapshot",{cache:"no-store"});
  const payload=await response.json();
  const s=payload.snapshot||{};

  document.getElementById("updated").textContent=
    `Updated ${s.generated_at||"unknown"}`;
  document.getElementById("health").textContent=
    s.company_health||"unknown";
  document.getElementById("score").textContent=
    s.company_score??0;
  document.getElementById("pipeline").textContent=
    money(s.crm?.pipeline_value);
  document.getElementById("cash").textContent=
    money(s.finance?.net_cash_position);
  document.getElementById("projects").textContent=
    s.projects?.active_projects??0;
  document.getElementById("followups").textContent=
    s.sales?.pending_followups??0;

  const f=s.finance||{};
  document.getElementById("finance").innerHTML=
    item("Total invoiced",money(f.total_invoiced))+
    item("Cash received",money(f.cash_received))+
    item("Accounts receivable",money(f.accounts_receivable))+
    item("Recorded expenses",money(f.recorded_expenses));

  document.getElementById("recommendations").innerHTML=
    (s.recommendations||[]).map(r=>
      item(
        r.title,
        r.detail,
        `<br><small class="priority-${r.priority}">Priority: ${r.priority}</small>`
      )
    ).join("")||item("No recommendations","No data available.");

  document.getElementById("activity").innerHTML=
    (s.recent_activity||[]).slice().reverse().map(a=>
      item(a.title||a.activity_type, a.created_at||"")
    ).join("")||item("No activity","No activity recorded yet.");
}

document.getElementById("refresh").addEventListener("click",async()=>{
  await fetch("/api/refresh",{method:"POST"});
  await load();
});

load().catch(error=>{
  document.getElementById("updated").textContent=`Error: ${error}`;
});
