/* Starter data — GitHub Actions will overwrite this automatically each morning. */
window.BRIEFING = {
  date: "Saturday, July 18, 2026",
  asOf: "Data as of Fri Jul 17 close",
  updated: "Jul 18, 2026 · 7:00 AM ICT",
  topStory: "A deepening AI and semiconductor selloff dragged global markets lower into the weekend. Chip stocks led declines across the US and Asia, while energy was the lone bright spot as oil climbed on Middle East tension.",
  sections: [
    { icon:"🇺🇸", title:"US Markets", span:false, rows:[
      { name:"S&P 500", lvl:"7,457.69", chg:"-1.0%", dir:"down" },
      { name:"Nasdaq Composite", lvl:"25,520.24", chg:"-1.4%", dir:"down" },
      { name:"Dow Jones", lvl:"52,146.42", chg:"-0.8%", dir:"down" },
      { name:"PHLX Semis (SOX)", lvl:"—", chg:"-4%+", dir:"down" },
    ], note:"All three indexes posted weekly losses. Netflix fell ~9% after hours on soft Q3 guidance." },

    { icon:"🌏", title:"Asia-Pacific", span:false, rows:[
      { name:"Nikkei 225 (Tokyo)", lvl:"—", chg:"-5.0%", dir:"down" },
      { name:"Hang Seng", lvl:"—", chg:"lower", dir:"down" },
      { name:"Shanghai Composite", lvl:"—", chg:"-4.0%", dir:"down" },
      { name:"Kospi (Seoul)", lvl:"Holiday", chg:"closed", dir:"flat" },
    ], note:"Tokyo's worst session in months as the AI trade unwound across the region." },

    { icon:"🇪🇺", title:"Europe & Global", span:false, rows:[
      { name:"FTSE 100", lvl:"—", chg:"mild", dir:"flat" },
      { name:"DAX", lvl:"—", chg:"mild", dir:"flat" },
    ], note:"European indices carry less AI/tech weight and held up better on a relative basis." },

    { icon:"💻", title:"Tech / AI Theme", span:false, rows:[],
      note:"The week's story is an <strong>AI-trade unwind</strong> — chipmakers hit hardest on stretched valuations and rotation. Traders are split: some position for a Nvidia bounce, others see another leg down. Watch for stabilization at the US open." },

    { icon:"💵", title:"FX & Rates", span:false, rows:[
      { name:"US 10-yr Treasury", lvl:"4.55%", chg:"yield", dir:"flat" },
      { name:"US 2-yr Treasury", lvl:"4.18%", chg:"yield", dir:"flat" },
      { name:"USD/THB", lvl:"~32.5", chg:"live", dir:"flat" },
    ], note:"Baht level pulled fresh each morning." },

    { icon:"🛢️", title:"Commodities", span:false, rows:[
      { name:"Brent Crude", lvl:"$86.09", chg:"+1.7%", dir:"up" },
      { name:"Gold", lvl:"—", chg:"lower", dir:"down" },
    ], note:"Crude up on Iran / Strait of Hormuz tension; gold slid to Nov '25 levels." },

    { icon:"📅", title:"Macro Watch", span:true, rows:[],
      note:"Central-bank commentary and any fresh inflation/jobs prints; Middle East energy-supply headlines remain the key swing factor for risk sentiment." },
  ],
  sources: [
    { label:"Stooq (market data)", url:"https://stooq.com" },
    { label:"Yahoo Finance — Markets", url:"https://finance.yahoo.com/markets/" },
    { label:"CNBC Markets", url:"https://www.cnbc.com/markets/" },
  ]
};
