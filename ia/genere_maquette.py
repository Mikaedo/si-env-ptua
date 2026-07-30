# -*- coding: utf-8 -*-
"""Genere la maquette complete SI-ENV avec 12 ecrans."""

CSS = """@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
*{margin:0;padding:0;box-sizing:border-box;font-family:'Inter',system-ui,sans-serif}
:root{--green:#006B3F;--green-dark:#004D2D;--green-light:#E8F5EE;--orange:#F7941D;--orange-light:#FFF4E6;--gray-50:#FAFAFA;--gray-100:#F5F5F5;--gray-200:#EEEEEE;--gray-400:#BDBDBD;--gray-600:#757575;--gray-800:#424242;--red:#E53935;--red-light:#FFEBEE;--blue:#1976D2;--blue-light:#E3F2FD;--white:#FFF;--shadow:0 2px 12px rgba(0,0,0,.06);--shadow-lg:0 8px 32px rgba(0,0,0,.08)}
body{background:#ECEFF1;display:flex;flex-wrap:wrap;gap:24px;padding:30px;justify-content:center}
.tw{width:100%;text-align:center;margin-bottom:8px}.tw h1{font-size:28px;font-weight:800;color:var(--green)}.tw p{font-size:14px;color:var(--gray-600);margin-top:4px}
.ph{width:320px;height:660px;border-radius:36px;background:#1a1a1a;padding:8px;box-shadow:0 12px 48px rgba(0,0,0,.12);position:relative}
.sc{width:100%;height:100%;border-radius:28px;overflow:hidden;background:var(--gray-50);display:flex;flex-direction:column;position:relative}
.nt{position:absolute;top:8px;left:50%;transform:translateX(-50%);width:100px;height:24px;background:#1a1a1a;border-radius:0 0 14px 14px;z-index:100}
.sb{height:36px;display:flex;align-items:center;justify-content:space-between;padding:0 20px;font-size:12px;font-weight:600;color:var(--gray-800);background:var(--white);padding-top:4px}
.sbr{display:flex;gap:4px;align-items:center}.sbr svg{width:14px;height:14px}
.ab{background:var(--white);padding:12px 20px;display:flex;align-items:center;gap:12px;border-bottom:1px solid var(--gray-200)}
.ab .lb{width:40px;height:40px;border-radius:12px;background:linear-gradient(135deg,var(--green),var(--green-dark));display:flex;align-items:center;justify-content:center;flex-shrink:0}
.ab .lb svg{width:22px;height:22px}.ab h2{font-size:17px;font-weight:700;color:var(--gray-800)}.ab p{font-size:11px;color:var(--gray-600);margin-top:1px}
.ab .nf{width:36px;height:36px;border-radius:10px;background:var(--gray-100);display:flex;align-items:center;justify-content:center;margin-left:auto;cursor:pointer;position:relative}
.ab .nf svg{width:18px;height:18px;color:var(--gray-600)}.ab .nf .dt{position:absolute;top:8px;right:8px;width:8px;height:8px;border-radius:50%;background:var(--orange);border:2px solid var(--white)}
.ab .bk{width:36px;height:36px;border-radius:10px;background:var(--gray-100);display:flex;align-items:center;justify-content:center;cursor:pointer}
.ab .bk svg{width:20px;height:20px;color:var(--gray-800)}
.cn{flex:1;overflow-y:auto;padding:16px 20px}.cn::-webkit-scrollbar{display:none}
.nb{height:64px;background:var(--white);border-top:1px solid var(--gray-200);display:flex;justify-content:space-around;align-items:center;padding-bottom:4px}
.ni{display:flex;flex-direction:column;align-items:center;gap:3px;cursor:pointer;position:relative;padding-top:4px}
.ni svg{width:22px;height:22px;color:var(--gray-400)}.ni span{font-size:10px;font-weight:500;color:var(--gray-400)}
.ni.act svg{color:var(--green)}.ni.act span{color:var(--green);font-weight:600}
.ni.act::before{content:'';position:absolute;top:0;width:24px;height:3px;border-radius:0 0 3px 3px;background:var(--green)}
.cd{background:var(--white);border-radius:16px;padding:16px;box-shadow:var(--shadow);margin-bottom:12px}
.ct{font-size:13px;font-weight:700;color:var(--gray-800);margin-bottom:10px;display:flex;align-items:center;gap:6px}
.ct svg{width:16px;height:16px;color:var(--green)}
.cp{display:inline-flex;align-items:center;gap:4px;padding:4px 10px;border-radius:20px;font-size:10px;font-weight:600}
.cp.g{background:var(--green-light);color:var(--green)}.cp.o{background:var(--orange-light);color:var(--orange)}.cp.r{background:var(--red-light);color:var(--red)}.cp.b{background:var(--blue-light);color:var(--blue)}
.bt{width:100%;padding:14px;border:none;border-radius:12px;font-size:14px;font-weight:600;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:8px}
.bt-p{background:var(--green);color:var(--white)}.bt-s{background:var(--gray-100);color:var(--gray-800)}.bt-r{background:var(--red-light);color:var(--red)}
.bt svg{width:18px;height:18px}
.ig{margin-bottom:14px}.il{display:block;font-size:12px;font-weight:600;color:var(--gray-600);margin-bottom:6px}
.ip{width:100%;padding:13px 16px;border:1.5px solid var(--gray-200);border-radius:12px;font-size:14px;outline:none;background:var(--gray-50);color:var(--gray-800)}
.ip:focus{border-color:var(--green);background:var(--white)}select.ip{cursor:pointer}
.sg{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:14px}
.sci{background:var(--white);border-radius:14px;padding:14px;box-shadow:var(--shadow);display:flex;align-items:center;gap:10px}
.sci .si{width:38px;height:38px;border-radius:10px;display:flex;align-items:center;justify-content:center;flex-shrink:0}.sci .si svg{width:20px;height:20px}
.sci .sn{font-size:20px;font-weight:800;color:var(--gray-800);line-height:1}.sci .sl{font-size:10px;color:var(--gray-600);margin-top:2px}
.li{display:flex;align-items:center;gap:12px;padding:14px 0;border-bottom:1px solid var(--gray-100)}.li:last-child{border-bottom:none}
.li .lic{width:40px;height:40px;border-radius:12px;display:flex;align-items:center;justify-content:center;flex-shrink:0}.li .lic svg{width:20px;height:20px}
.li .lin{flex:1;min-width:0}.li .lin h4{font-size:13px;font-weight:600;color:var(--gray-800);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.li .lin p{font-size:11px;color:var(--gray-600);margin-top:2px}
.fb{position:absolute;bottom:76px;right:20px;width:56px;height:56px;border-radius:18px;background:var(--green);color:var(--white);border:none;cursor:pointer;box-shadow:0 6px 20px rgba(0,107,63,.3);display:flex;align-items:center;justify-content:center;z-index:50}.fb svg{width:24px;height:24px}
.iab{background:linear-gradient(135deg,var(--green-light),var(--white));border:1.5px solid var(--green);border-radius:14px;padding:14px;margin:12px 0;text-align:center}
.iab .ii{width:44px;height:44px;border-radius:12px;background:var(--green);display:flex;align-items:center;justify-content:center;margin:0 auto 8px}.iab .ii svg{width:24px;height:24px;color:var(--white)}
.iab h4{font-size:13px;font-weight:700;color:var(--green);margin-bottom:4px}.iab p{font-size:11px;color:var(--gray-600);line-height:1.5}
.pa{width:100%;height:140px;border-radius:14px;margin-bottom:12px;background:linear-gradient(135deg,var(--gray-100),var(--gray-200));border:2px dashed var(--gray-400);display:flex;flex-direction:column;align-items:center;justify-content:center;gap:6px}
.pa svg{width:36px;height:36px;color:var(--gray-400)}.pa span{font-size:12px;color:var(--gray-600)}
.mc{flex:1;position:relative;background:linear-gradient(180deg,#D7E8D4,#C5DDB8);overflow:hidden}
.mr{position:absolute;background:var(--white);box-shadow:0 1px 3px rgba(0,0,0,.1)}
.mp{position:absolute;width:32px;height:32px;display:flex;align-items:center;justify-content:center}.mp svg{width:28px;height:28px;filter:drop-shadow(0 2px 4px rgba(0,0,0,.2))}
.mi2{position:absolute;bottom:16px;left:16px;right:16px;background:var(--white);border-radius:14px;padding:12px 16px;box-shadow:var(--shadow-lg);display:flex;align-items:center;gap:10px}
.mi2 .mii{width:36px;height:36px;border-radius:10px;background:var(--green-light);display:flex;align-items:center;justify-content:center}.mi2 .mii svg{width:18px;height:18px;color:var(--green)}
.mi2 .mit{flex:1}.mi2 .mit h4{font-size:12px;font-weight:700;color:var(--gray-800)}.mi2 .mit p{font-size:10px;color:var(--gray-600)}
.br{margin-bottom:10px}.bl{display:flex;justify-content:space-between;font-size:11px;margin-bottom:4px}.bl span:first-child{color:var(--gray-800);font-weight:500}.bl span:last-child{color:var(--gray-600)}
.bt2{height:8px;background:var(--gray-100);border-radius:4px;overflow:hidden}.bf{height:100%;border-radius:4px}
.cbs{display:flex;align-items:flex-end;gap:10px;height:100px;margin-top:12px}.cbc{flex:1;display:flex;flex-direction:column;align-items:center;gap:4px}.cbb{width:100%;border-radius:6px 6px 0 0}.cbc span{font-size:10px;color:var(--gray-600)}
.ph2{text-align:center;padding:20px 0}
.av{width:76px;height:76px;border-radius:24px;background:linear-gradient(135deg,var(--green),var(--green-dark));margin:0 auto 10px;display:flex;align-items:center;justify-content:center}.av svg{width:36px;height:36px;color:var(--white)}
.ph2 h3{font-size:16px;font-weight:700;color:var(--gray-800)}.ph2 p{font-size:12px;color:var(--gray-600);margin-top:2px}
.mn{display:flex;align-items:center;gap:14px;padding:14px 16px;cursor:pointer;border-bottom:1px solid var(--gray-100)}.mn:hover{background:var(--gray-50)}
.mn .mm{width:36px;height:36px;border-radius:10px;display:flex;align-items:center;justify-content:center}.mn .mm svg{width:18px;height:18px}
.mn .mt2{flex:1}.mn .mt2 h4{font-size:13px;font-weight:600;color:var(--gray-800)}.mn .mt2 p{font-size:11px;color:var(--gray-600);margin-top:1px}
.mn .ma svg{width:16px;height:16px;color:var(--gray-400)}
.sy{display:inline-flex;align-items:center;gap:4px;background:var(--orange-light);color:var(--orange);padding:3px 8px;border-radius:6px;font-size:10px;font-weight:600;margin-left:8px}.sy svg{width:12px;height:12px}
.pg{height:6px;background:var(--gray-100);border-radius:3px;overflow:hidden;margin:8px 0}.pf{height:100%;background:var(--green);border-radius:3px;transition:width .3s}
.dt-card{background:var(--white);border-radius:16px;overflow:hidden;box-shadow:var(--shadow);margin-bottom:12px}
.dt-img{width:100%;height:160px;background:linear-gradient(135deg,var(--gray-100),var(--gray-200));display:flex;align-items:center;justify-content:center}
.dt-img svg{width:48px;height:48px;color:var(--gray-400)}
.dt-body{padding:16px}
.dt-row{display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid var(--gray-100)}.dt-row:last-child{border-bottom:none}
.dt-row .dk{font-size:12px;color:var(--gray-600)}.dt-row .dv{font-size:12px;font-weight:600;color:var(--gray-800)}
.fl-row{display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap}
.fl-chip{padding:8px 14px;border-radius:20px;font-size:12px;font-weight:600;cursor:pointer;border:1.5px solid var(--gray-200);background:var(--white);color:var(--gray-600)}
.fl-chip.act{background:var(--green);color:var(--white);border-color:var(--green)}
.al-item{display:flex;gap:12px;padding:14px 0;border-bottom:1px solid var(--gray-100)}
.al-icon{width:40px;height:40px;border-radius:12px;display:flex;align-items:center;justify-content:center;flex-shrink:0}.al-icon svg{width:20px;height:20px}
.al-info{flex:1}.al-info h4{font-size:13px;font-weight:600;color:var(--gray-800)}.al-info p{font-size:11px;color:var(--gray-600);margin-top:2px;line-height:1.4}
.al-time{font-size:10px;color:var(--gray-400);white-space:nowrap}
.tg{display:flex;align-items:center;justify-content:space-between;padding:14px 0;border-bottom:1px solid var(--gray-100)}
.tg-info h4{font-size:13px;font-weight:600;color:var(--gray-800)}.tg-info p{font-size:11px;color:var(--gray-600);margin-top:2px}
.sw{width:44px;height:24px;border-radius:12px;background:var(--gray-200);position:relative;cursor:pointer;transition:.2s}
.sw.on{background:var(--green)}
.sw::after{content:'';position:absolute;top:2px;left:2px;width:20px;height:20px;border-radius:50%;background:var(--white);transition:.2s;box-shadow:0 1px 3px rgba(0,0,0,.2)}
.sw.on::after{left:22px}
.pw-wrap{position:relative}
.pw-toggle{position:absolute;right:14px;top:50%;transform:translateY(-50%);cursor:pointer;color:var(--gray-400);display:flex;align-items:center}.pw-toggle svg{width:20px;height:20px}
.hint{font-size:10px;color:var(--gray-400);margin-top:6px;line-height:1.6}
.hint b{color:var(--gray-600);font-weight:600}
.link-btn{background:none;border:none;font-size:12px;color:var(--green);font-weight:600;cursor:pointer;padding:0}
.err-msg{background:var(--red-light);color:var(--red);font-size:12px;font-weight:600;padding:10px 14px;border-radius:10px;margin-bottom:14px;display:flex;align-items:center;gap:8px}.err-msg svg{width:18px;height:18px;flex-shrink:0}
.gps-toggle{display:flex;align-items:center;gap:8px;margin-top:6px}.gps-toggle label{font-size:11px;color:var(--gray-600);cursor:pointer;display:flex;align-items:center;gap:4px}
.success-card{background:var(--white);border-radius:20px;padding:32px 24px;text-align:center;box-shadow:var(--shadow-lg);margin:20px 0}
.success-icon{width:72px;height:72px;border-radius:24px;background:var(--green);display:flex;align-items:center;justify-content:center;margin:0 auto 16px;box-shadow:0 8px 24px rgba(0,107,63,.2)}.success-icon svg{width:36px;height:36px}
"""

# SVG icons
IC = {
 'wifi': '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M1 9l2 2c4.97-4.97 13.03-4.97 18 0l2-2C16.93 2.93 7.08 2.93 1 9z"/></svg>',
 'batt': '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M15.67 4H14V2h-4v2H8.33C7.6 4 7 4.6 7 5.33v15.33C7 21.4 7.6 22 8.33 22h7.33c.74 0 1.34-.6 1.34-1.33V5.33C17 4.6 16.4 4 15.67 4z"/></svg>',
 'leaf': '<svg viewBox="0 0 24 24" fill="white"><path d="M17 8C8 10 5.9 16.17 3.82 21.34l1.89.66.95-2.3c.48.17.98.3 1.34.3C19 20 22 3 22 3c-1 2-8 2.25-13 3.25S2 11.5 2 13.5s1.75 3.75 1.75 3.75C7 8 17 8 17 8z"/></svg>',
 'bell': '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 22c1.1 0 2-.9 2-2h-4c0 1.1.89 2 2 2zm6-6v-5c0-3.07-1.64-5.64-4.5-6.32V4c0-.83-.67-1.5-1.5-1.5s-1.5.67-1.5 1.5v.68C7.63 5.36 6 7.92 6 11v5l-2 2v1h16v-1l-2-2z"/></svg>',
 'back': '<svg viewBox="0 0 24 24" fill="var(--gray-800)" width="20" height="20"><path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/></svg>',
 'pin': '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/></svg>',
 'doc': '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z"/></svg>',
 'chart': '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M3.5 18.49l6-6.01 4 4L22 6.92l-1.41-1.41-7.09 7.97-4-4L2 16.99z"/></svg>',
 'user': '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg>',
 'plus': '<svg viewBox="0 0 24 24" fill="white"><path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/></svg>',
 'cam': '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 15.2c1.84 0 3.2-1.36 3.2-3.2s-1.36-3.2-3.2-3.2-3.2 1.36-3.2 3.2 1.36 3.2 3.2 3.2zM9 2L7.17 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2h-3.17L15 2H9z"/></svg>',
 'brain': '<svg viewBox="0 0 24 24" fill="white"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/></svg>',
 'trash': '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/></svg>',
 'water': '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2c-4 0-8 .5-8 4v9.5C4 17.43 5.57 19 7.5 19L6 20.5v.5h12v-.5L16.5 19c1.93 0 3.5-1.57 3.5-3.5V6c0-3.5-4-4-8-4z"/></svg>',
 'check': '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg>',
 'warn': '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/></svg>',
 'info': '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 14h-2v-4h2v4zm0-6h-2V7h2v4z"/></svg>',
 'save': '<svg viewBox="0 0 24 24" fill="white"><path d="M17 3H5c-1.11 0-2 .9-2 2v14c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V7l-4-4zm-5 16c-1.66 0-3-1.34-3-3s1.34-3 3-3 3 1.34 3 3-1.34 3-3 3zm3-10H5V5h10v4z"/></svg>',
 'sync': '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 4V1L8 5l4 4V6c3.31 0 6 2.69 6 6 0 1.01-.25 1.97-.7 2.8l1.46 1.46C19.54 15.03 20 13.57 20 12c0-4.42-3.58-8-8-8z"/></svg>',
 'mail': '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M20 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z"/></svg>',
 'phone': '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M17 1.01L7 1c-1.1 0-2 .9-2 2v18c0 1.1.9 2 2 2h10c1.1 0 2-.9 2-2v-18c0-1.1-.9-1.99-2-1.99zM17 19H7V5h10v14z"/></svg>',
 'gear': '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M19.14 12.94c.04-.3.06-.61.06-.94 0-.32-.02-.64-.07-.94l2.03-1.58c.18-.14.23-.41.12-.61l-1.92-3.32c-.12-.22-.37-.29-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54c-.04-.24-.24-.41-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.05.3-.09.63-.09.94s.02.64.07.94l-2.03 1.58c-.18.14-.23.41-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z"/></svg>',
 'logout': '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M17 7l-1.41 1.41L18.17 11H8v2h10.17l-2.58 2.58L17 17l5-5zM4 5h8V3H4c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h8v-2H4V5z"/></svg>',
 'lock': '<svg viewBox="0 0 24 24" fill="white"><path d="M18 8h-1V6c0-2.76-2.24-5-5-5S7 3.24 7 6v2H6c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V10c0-1.1-.9-2-2-2zm-6 9c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2zm3.1-9H8.9V6c0-1.71 1.39-3.1 3.1-3.1 1.71 0 3.1 1.39 3.1 3.1v2z"/></svg>',
 'fwd': '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z"/></svg>',
 'cloud': '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M19.35 10.04C18.67 6.59 15.64 4 12 4 9.11 4 6.6 5.64 5.35 8.04 2.34 8.36 0 10.91 0 14c0 3.31 2.69 6 6 6h13c2.76 0 5-2.24 5-5 0-2.64-2.05-4.78-4.65-4.96z"/></svg>',
 'gps': '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 8c-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4-1.79-4-4-4zm8.94 3A8.994 8.994 0 0 0 13 3.06V1h-2v2.06A8.994 8.994 0 0 0 3.06 11H1v2h2.06A8.994 8.994 0 0 0 11 20.94V23h2v-2.06A8.994 8.994 0 0 0 20.94 13H23v-2h-2.06z"/></svg>',
 'dust': '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z"/></svg>',
 'eye': '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"/></svg>',
 'eyeoff': '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 7c2.76 0 5 2.24 5 5 0 .65-.13 1.26-.36 1.83l2.92 2.92c1.51-1.26 2.7-2.89 3.43-4.75-1.73-4.39-6-7.5-11-7.5-1.84 0-3.58.43-5.12 1.2l2.15 2.15C10.2 7.18 11.08 7 12 7zM2 4.27l2.28 2.28.51.51C1.08 8.63 0 12.05 0 12.05s1.99 5.08 6 7.5c1.61.97 3.47 1.45 5.4 1.45 1.66 0 3.22-.36 4.61-.99l.49.49L19.73 22 21 20.73 3.27 3 2 4.27zM7.53 9.8l1.55 1.55c-.05.21-.08.43-.08.65 0 1.66 1.34 3 3 3 .22 0 .44-.03.65-.08l1.55 1.55c-.67.33-1.41.53-2.2.53-2.76 0-5-2.24-5-5 0-.79.2-1.53.53-2.2z"/></svg>',
 'veg': '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M17 8C8 10 5.9 16.17 3.82 21.34l1.89.66.95-2.3c.48.17.98.3 1.34.3C19 20 22 3 22 3c-1 2-8 2.25-13 3.25S2 11.5 2 13.5s1.75 3.75 1.75 3.75C7 8 17 8 17 8z"/></svg>',
 'success': '<svg viewBox="0 0 24 24" fill="white"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg>',
 'edit': '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34c-.39-.39-1.02-.39-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/></svg>',
}

def sb():
    return f'<div class="sb"><span>9:41</span><div class="sbr">{IC["wifi"]}{IC["batt"]}</div></div>'

def navbar(active=""):
    items = [("pin","Carte"),("doc","Signalements"),("chart","Stats"),("user","Profil")]
    out = '<div class="nb">'
    for icon,label in items:
        cls = ' class="ni act"' if label==active else ' class="ni"'
        out += f'<div{cls}>{IC[icon]}<span>{label}</span></div>'
    out += '</div>'
    return out

def appbar(title, sub, icon="leaf", back=False, notif=False):
    bk = f'<div class="bk">{IC["back"]}</div>' if back else ''
    nf = ''
    if notif:
        nf = f'<div class="nf">{IC["bell"]}<div class="dt"></div></div>'
    return f'''<div class="ab">{bk}<div class="lb">{IC[icon]}</div><div><h2>{title}</h2><p>{sub}</p></div>{nf}</div>'''

# === ECRANS ===
screens = []

# 1. LOGIN
screens.append(f'''<div class="ph"><div class="nt"></div><div class="sc">
{sb()}
<div style="flex:1;display:flex;flex-direction:column;justify-content:center;padding:32px 28px;background:var(--white)">
<div style="text-align:center;margin-bottom:36px">
<div style="width:80px;height:80px;border-radius:24px;background:linear-gradient(135deg,var(--green),var(--green-dark));margin:0 auto 16px;display:flex;align-items:center;justify-content:center;box-shadow:0 8px 24px rgba(0,107,63,.2)">{IC["leaf"]}</div>
<h1 style="font-size:24px;font-weight:800;color:var(--gray-800)">SI-ENV</h1>
<p style="font-size:12px;color:var(--gray-600);margin-top:4px">Suivi Environnemental · PTUA</p>
<div style="width:40px;height:3px;border-radius:2px;background:var(--orange);margin:12px auto 0"></div>
</div>
<div class="err-msg">{IC["warn"]} Email ou mot de passe incorrect</div>
<div class="ig"><label class="il">Adresse email</label><input class="ip" type="email" placeholder="agent@ageroute.ci" value="g.konanbouo@ageroute.ci"></div>
<div class="ig"><label class="il">Mot de passe</label><div class="pw-wrap"><input class="ip" type="password" placeholder="· · · · · · · ·" style="padding-right:44px"><div class="pw-toggle">{IC["eye"]}</div></div></div>
<button class="bt bt-p" style="margin-top:8px">{IC["lock"]} Se connecter</button>
<p style="text-align:center;margin-top:14px"><button class="link-btn">Mot de passe oublie ?</button></p>
<p style="text-align:center;font-size:11px;color:var(--gray-400);margin-top:16px">AGEROUTE · CC-PTUA v1.0</p>
</div></div></div>''')

# 2. PREMIERE CONNEXION - DEFINIR SON MOT DE PASSE
screens.append(f'''<div class="ph"><div class="nt"></div><div class="sc">
{sb()}
{appbar("Bienvenue","Definissez votre mot de passe","lock",back=True)}
<div class="cn">
<div class="cd" style="text-align:center;padding:20px">
<div style="width:56px;height:56px;border-radius:16px;background:var(--green-light);display:flex;align-items:center;justify-content:center;margin:0 auto 12px">
<svg viewBox="0 0 24 24" fill="var(--green)" width="28" height="28"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg>
</div>
<p style="font-size:12px;color:var(--gray-600);line-height:1.5">Votre compte a ete cree par l'administrateur. Pour votre premiere connexion, choisissez votre mot de passe.</p>
</div>
<div class="ig"><label class="il">Nouveau mot de passe</label><div class="pw-wrap"><input class="ip" type="password" placeholder="Min. 8 caracteres" style="padding-right:44px"><div class="pw-toggle">{IC["eyeoff"]}</div></div><div class="hint"><b>8 caracteres min.</b> · 1 majuscule · 1 chiffre · 1 caractere special</div></div>
<div class="ig"><label class="il">Confirmer le mot de passe</label><div class="pw-wrap"><input class="ip" type="password" placeholder="Repeter" style="padding-right:44px"><div class="pw-toggle">{IC["eye"]}</div></div></div>
<button class="bt bt-p" style="margin-top:8px">{IC["check"]} Definir mon mot de passe</button>
</div></div></div>''')

# 2b. MOT DE PASSE OUBLIE - ETAPE 1: EMAIL
screens.append(f'''<div class="ph"><div class="nt"></div><div class="sc">
{sb()}
{appbar("Mot de passe oublie","Etape 1/3 · Email","lock",back=True)}
<div class="cn">
<div class="cd" style="text-align:center;padding:20px">
<div style="width:56px;height:56px;border-radius:16px;background:var(--orange-light);display:flex;align-items:center;justify-content:center;margin:0 auto 12px">
{IC["mail"]}
</div>
<p style="font-size:12px;color:var(--gray-600);line-height:1.5">Entrez votre adresse email professionnelle. Un code de verification vous sera envoye.</p>
</div>
<div class="ig"><label class="il">Adresse email</label><input class="ip" type="email" placeholder="agent@ageroute.ci"></div>
<button class="bt bt-p" style="margin-top:8px">{IC["mail"]} Envoyer le code</button>
</div></div></div>''')

# 2c. MOT DE PASSE OUBLIE - ETAPE 2: CODE DE VERIFICATION
screens.append(f'''<div class="ph"><div class="nt"></div><div class="sc">
{sb()}
{appbar("Mot de passe oublie","Etape 2/3 · Verification","lock",back=True)}
<div class="cn">
<div class="cd" style="text-align:center;padding:20px">
<div style="width:56px;height:56px;border-radius:16px;background:var(--orange-light);display:flex;align-items:center;justify-content:center;margin:0 auto 12px">
<svg viewBox="0 0 24 24" fill="var(--orange)" width="28" height="28"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>
</div>
<p style="font-size:12px;color:var(--gray-600);line-height:1.5">Un code a 6 chiffres a ete envoye a <b>g.konanbouo@ageroute.ci</b></p>
</div>
<div class="ig" style="text-align:center">
<label class="il" style="text-align:center">Code de verification</label>
<div style="display:flex;gap:8px;justify-content:center">
<input class="ip" style="width:40px;text-align:center;font-size:18px;font-weight:700;padding:13px 0" maxlength="1" value="">
<input class="ip" style="width:40px;text-align:center;font-size:18px;font-weight:700;padding:13px 0" maxlength="1" value="">
<input class="ip" style="width:40px;text-align:center;font-size:18px;font-weight:700;padding:13px 0" maxlength="1" value="">
<input class="ip" style="width:40px;text-align:center;font-size:18px;font-weight:700;padding:13px 0" maxlength="1" value="">
<input class="ip" style="width:40px;text-align:center;font-size:18px;font-weight:700;padding:13px 0" maxlength="1" value="">
<input class="ip" style="width:40px;text-align:center;font-size:18px;font-weight:700;padding:13px 0" maxlength="1" value="">
</div>
</div>
<p style="text-align:center;font-size:11px;color:var(--gray-400);margin-top:8px">Renvoyer le code (0:59)</p>
<button class="bt bt-p" style="margin-top:12px">{IC["check"]} Verifier</button>
</div></div></div>''')

# 2d. MOT DE PASSE OUBLIE - ETAPE 3: NOUVEAU MOT DE PASSE
screens.append(f'''<div class="ph"><div class="nt"></div><div class="sc">
{sb()}
{appbar("Mot de passe oublie","Etape 3/3 · Nouveau mot de passe","lock",back=True)}
<div class="cn">
<div class="cd" style="text-align:center;padding:20px">
<div style="width:56px;height:56px;border-radius:16px;background:var(--green-light);display:flex;align-items:center;justify-content:center;margin:0 auto 12px">
<svg viewBox="0 0 24 24" fill="var(--green)" width="28" height="28"><path d="M18 8h-1V6c0-2.76-2.24-5-5-5S7 3.24 7 6v2H6c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V10c0-1.1-.9-2-2-2zm-6 9c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2zm3.1-9H8.9V6c0-1.71 1.39-3.1 3.1-3.1 1.71 0 3.1 1.39 3.1 3.1v2z"/></svg>
</div>
<p style="font-size:12px;color:var(--gray-600);line-height:1.5">Choisissez un nouveau mot de passe pour votre compte.</p>
</div>
<div class="ig"><label class="il">Nouveau mot de passe</label><div class="pw-wrap"><input class="ip" type="password" placeholder="Min. 8 caracteres" style="padding-right:44px"><div class="pw-toggle">{IC["eyeoff"]}</div></div><div class="hint"><b>8 caracteres min.</b> · 1 majuscule · 1 chiffre · 1 caractere special</div></div>
<div class="ig"><label class="il">Confirmer le mot de passe</label><div class="pw-wrap"><input class="ip" type="password" placeholder="Repeter" style="padding-right:44px"><div class="pw-toggle">{IC["eye"]}</div></div></div>
<button class="bt bt-p" style="margin-top:8px">{IC["check"]} Reinitialiser mon mot de passe</button>
</div></div></div>''')

# 3. CARTE
screens.append(f'''<div class="ph"><div class="nt"></div><div class="sc">
{sb()}
{appbar("Carte des chantiers","PTUA · Abidjan","leaf",notif=True)}
<div class="mc">
<div class="mr" style="width:220px;height:5px;top:28%;left:5%;transform:rotate(22deg);border-radius:3px"></div>
<div class="mr" style="width:160px;height:5px;top:52%;left:25%;transform:rotate(-12deg);border-radius:3px"></div>
<div class="mr" style="width:5px;height:180px;top:15%;left:55%;border-radius:3px"></div>
<div class="mr" style="width:120px;height:5px;top:70%;left:10%;transform:rotate(8deg);border-radius:3px"></div>
<div class="mp" style="top:22%;left:18%"><svg viewBox="0 0 24 24" fill="#E53935"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/></svg></div>
<div class="mp" style="top:42%;left:52%"><svg viewBox="0 0 24 24" fill="#F7941D"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/></svg></div>
<div class="mp" style="top:62%;left:28%"><svg viewBox="0 0 24 24" fill="#006B3F"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/></svg></div>
<div class="mp" style="top:32%;left:68%"><svg viewBox="0 0 24 24" fill="#F7941D"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/></svg></div>
<div class="mi2"><div class="mii">{IC["pin"]}</div><div class="mit"><h4>4 chantiers actifs</h4><p>12 signalements · 2 urgents</p></div></div>
<div style="position:absolute;bottom:16px;right:100px;background:var(--white);border-radius:12px;padding:10px 12px;box-shadow:var(--shadow);display:flex;flex-direction:column;gap:6px">
<div style="display:flex;align-items:center;gap:6px;font-size:10px;color:var(--gray-800);font-weight:600"><span style="width:10px;height:10px;border-radius:50%;background:#E53935"></span>Eleve</div>
<div style="display:flex;align-items:center;gap:6px;font-size:10px;color:var(--gray-800);font-weight:600"><span style="width:10px;height:10px;border-radius:50%;background:#F7941D"></span>Modere</div>
<div style="display:flex;align-items:center;gap:6px;font-size:10px;color:var(--gray-800);font-weight:600"><span style="width:10px;height:10px;border-radius:50%;background:#006B3F"></span>Faible</div>
</div>
</div>
<button class="fb">{IC["plus"]}</button>
{navbar("Carte")}
</div></div>''')

# 4a. NOUVEAU SIGNALEMENT - DECHETS (avec IA)
screens.append(f'''<div class="ph"><div class="nt"></div><div class="sc">
{sb()}
{appbar("Nouveau signalement","Dechets de chantier","doc",back=True)}
<div class="cn">
<div class="pa" style="border-color:var(--green);background:linear-gradient(135deg,var(--green-light),var(--gray-100))">{IC["cam"]}<span style="color:var(--green);font-weight:600">Photo prise · analyse IA en cours...</span></div>
<div class="ig"><label class="il">Type de nuisance</label><select class="ip"><option>Dechets de chantier</option><option>Eaux stagnantes</option><option>Poussieres</option><option>Bruit</option><option>Degradation vegetation</option></select></div>
<div class="ig"><label class="il">Chantier concerne</label><select class="ip"><option>Pont de Bassam · Lot 1</option><option>Bd Latrille · Lot 3</option><option>Rocade Marcory · Lot 2</option></select></div>
<div class="ig"><label class="il">Coordonnees GPS</label><input class="ip" type="text" value="5.3600 N, 4.0083 W" style="color:var(--gray-600)"><div class="gps-toggle"><label><span class="sw on" style="width:32px;height:18px"></span> GPS auto</label><label style="margin-left:12px">Saisie manuelle si GPS indisponible</label></div></div>
<div class="ig"><label class="il">Description (optionnel)</label><input class="ip" type="text" placeholder="Accumulation pres du pont..."></div>
<div class="iab"><div class="ii">{IC["brain"]}</div><h4>Diagnostic IA · Dechets detectes</h4><p>YOLOv8n : 3 objets identifies (plastique, metal, organique)</p><p style="margin-top:4px">MobileNetV2 : Confiance 87%</p><p style="margin-top:6px"><span class="cp o">Criticite suggerée : Moderee</span></p></div>
<div class="ig" style="margin-top:12px"><label class="il">Confirmer la criticite</label><select class="ip"><option>Faible</option><option selected>Modere (suggeré par IA)</option><option>Eleve</option></select></div>
<button class="bt bt-p">{IC["save"]} Enregistrer le signalement</button>
</div></div></div>''')

# 4b. NOUVEAU SIGNALEMENT - EAUX STAGNANTES (sans IA)
screens.append(f'''<div class="ph"><div class="nt"></div><div class="sc">
{sb()}
{appbar("Nouveau signalement","Eaux stagnantes","water",back=True)}
<div class="cn">
<div class="pa">{IC["cam"]}<span>Toucher pour prendre une photo</span></div>
<div class="ig"><label class="il">Type de nuisance</label><select class="ip"><option>Dechets de chantier</option><option selected>Eaux stagnantes</option><option>Poussieres</option><option>Bruit</option><option>Degradation vegetation</option></select></div>
<div class="ig"><label class="il">Chantier concerne</label><select class="ip"><option>Pont de Bassam · Lot 1</option><option>Bd Latrille · Lot 3</option><option>Rocade Marcory · Lot 2</option></select></div>
<div class="ig"><label class="il">Coordonnees GPS</label><input class="ip" type="text" value="5.3600 N, 4.0083 W" style="color:var(--gray-600)"><div class="gps-toggle"><label><span class="sw on" style="width:32px;height:18px"></span> GPS auto</label><label style="margin-left:12px">Saisie manuelle si GPS indisponible</label></div></div>
<div class="ig"><label class="il">Description (optionnel)</label><input class="ip" type="text" placeholder="Stagnation apres pluie..."></div>
<div class="ig"><label class="il">Niveau de criticite</label><select class="ip"><option>Faible</option><option>Modere</option><option>Eleve</option></select><div class="hint">Evaluation manuelle par l'agent</div></div>
<button class="bt bt-p">{IC["save"]} Enregistrer le signalement</button>
</div></div></div>''')

# 4c. NOUVEAU SIGNALEMENT - POUSSIERES (sans IA)
screens.append(f'''<div class="ph"><div class="nt"></div><div class="sc">
{sb()}
{appbar("Nouveau signalement","Poussieres","dust",back=True)}
<div class="cn">
<div class="pa">{IC["cam"]}<span>Toucher pour prendre une photo</span></div>
<div class="ig"><label class="il">Type de nuisance</label><select class="ip"><option>Dechets de chantier</option><option>Eaux stagnantes</option><option selected>Poussieres</option><option>Bruit</option><option>Degradation vegetation</option></select></div>
<div class="ig"><label class="il">Chantier concerne</label><select class="ip"><option>Pont de Bassam · Lot 1</option><option>Bd Latrille · Lot 3</option><option>Rocade Marcory · Lot 2</option></select></div>
<div class="ig"><label class="il">Coordonnees GPS</label><input class="ip" type="text" value="5.3600 N, 4.0083 W" style="color:var(--gray-600)"><div class="gps-toggle"><label><span class="sw on" style="width:32px;height:18px"></span> GPS auto</label><label style="margin-left:12px">Saisie manuelle si GPS indisponible</label></div></div>
<div class="ig"><label class="il">Description (optionnel)</label><input class="ip" type="text" placeholder="Nuage de poussiere sur le chantier..."></div>
<div class="ig"><label class="il">Niveau de criticite</label><select class="ip"><option>Faible</option><option>Modere</option><option>Eleve</option></select><div class="hint">Evaluation manuelle par l'agent</div></div>
<button class="bt bt-p">{IC["save"]} Enregistrer le signalement</button>
</div></div></div>''')

# 4d. NOUVEAU SIGNALEMENT - BRUIT (sans IA)
screens.append(f'''<div class="ph"><div class="nt"></div><div class="sc">
{sb()}
{appbar("Nouveau signalement","Bruit","warn",back=True)}
<div class="cn">
<div class="pa">{IC["cam"]}<span>Toucher pour prendre une photo</span></div>
<div class="ig"><label class="il">Type de nuisance</label><select class="ip"><option>Dechets de chantier</option><option>Eaux stagnantes</option><option>Poussieres</option><option selected>Bruit</option><option>Degradation vegetation</option></select></div>
<div class="ig"><label class="il">Chantier concerne</label><select class="ip"><option>Pont de Bassam · Lot 1</option><option>Bd Latrille · Lot 3</option><option>Rocade Marcory · Lot 2</option></select></div>
<div class="ig"><label class="il">Coordonnees GPS</label><input class="ip" type="text" value="5.3600 N, 4.0083 W" style="color:var(--gray-600)"><div class="gps-toggle"><label><span class="sw on" style="width:32px;height:18px"></span> GPS auto</label><label style="margin-left:12px">Saisie manuelle si GPS indisponible</label></div></div>
<div class="ig"><label class="il">Description (optionnel)</label><input class="ip" type="text" placeholder="Bruit intense en dehors des heures..."></div>
<div class="ig"><label class="il">Niveau de criticite</label><select class="ip"><option>Faible</option><option>Modere</option><option>Eleve</option></select><div class="hint">Evaluation manuelle par l'agent</div></div>
<button class="bt bt-p">{IC["save"]} Enregistrer le signalement</button>
</div></div></div>''')

# 4e. NOUVEAU SIGNALEMENT - DEGRADATION VEGETATION (sans IA)
screens.append(f'''<div class="ph"><div class="nt"></div><div class="sc">
{sb()}
{appbar("Nouveau signalement","Degradation vegetation","veg",back=True)}
<div class="cn">
<div class="pa">{IC["cam"]}<span>Toucher pour prendre une photo</span></div>
<div class="ig"><label class="il">Type de nuisance</label><select class="ip"><option>Dechets de chantier</option><option>Eaux stagnantes</option><option>Poussieres</option><option>Bruit</option><option selected>Degradation vegetation</option></select></div>
<div class="ig"><label class="il">Chantier concerne</label><select class="ip"><option>Pont de Bassam · Lot 1</option><option>Bd Latrille · Lot 3</option><option>Rocade Marcory · Lot 2</option></select></div>
<div class="ig"><label class="il">Coordonnees GPS</label><input class="ip" type="text" value="5.3600 N, 4.0083 W" style="color:var(--gray-600)"><div class="gps-toggle"><label><span class="sw on" style="width:32px;height:18px"></span> GPS auto</label><label style="margin-left:12px">Saisie manuelle si GPS indisponible</label></div></div>
<div class="ig"><label class="il">Description (optionnel)</label><input class="ip" type="text" placeholder="Abattage ou degradation d'arbres..."></div>
<div class="ig"><label class="il">Niveau de criticite</label><select class="ip"><option>Faible</option><option>Modere</option><option>Eleve</option></select><div class="hint">Evaluation manuelle par l'agent</div></div>
<button class="bt bt-p">{IC["save"]} Enregistrer le signalement</button>
</div></div></div>''')

# 4f. CONFIRMATION SIGNALEMENT CREE
screens.append(f'''<div class="ph"><div class="nt"></div><div class="sc">
{sb()}
{appbar("Signalement cree","SIG-2026-0044","check",back=True)}
<div class="cn" style="display:flex;flex-direction:column;justify-content:center;flex:1">
<div class="success-card">
<div class="success-icon">{IC["success"]}</div>
<h3 style="font-size:18px;font-weight:800;color:var(--gray-800);margin-bottom:6px">Signalement enregistre</h3>
<p style="font-size:13px;color:var(--gray-600);line-height:1.5">Votre signalement a ete enregistre localement. Il sera synchronise des que le reseau sera disponible.</p>
<div class="cd" style="margin-top:16px;text-align:left">
<div class="dt-row"><span class="dk">Reference</span><span class="dv">SIG-2026-0044</span></div>
<div class="dt-row"><span class="dk">Type</span><span class="dv">Dechets de chantier</span></div>
<div class="dt-row"><span class="dk">Statut</span><span class="dv" style="color:var(--orange)">PENDING_SYNC</span></div>
</div>
</div>
<button class="bt bt-p" style="margin-bottom:8px">{IC["plus"]} Nouveau signalement</button>
<button class="bt bt-s">{IC["doc"]} Voir mes signalements</button>
</div></div></div>''')

# 5. LISTE SIGNALEMENTS
screens.append(f'''<div class="ph"><div class="nt"></div><div class="sc">
{sb()}
{appbar("Signalements","12 au total","doc",notif=True)}
<div class="cn" style="padding-top:12px">
<div class="ig" style="margin-bottom:12px"><div class="pw-wrap"><input class="ip" type="text" placeholder="Rechercher un signalement..." style="padding-right:44px"><div class="pw-toggle" style="color:var(--gray-400)">{IC["info"]}</div></div></div>
<div class="sg">
<div class="sci"><div class="si" style="background:var(--green-light)">{IC["check"]}</div><div><div class="sn">7</div><div class="sl">Traités</div></div></div>
<div class="sci"><div class="si" style="background:var(--orange-light)">{IC["warn"]}</div><div><div class="sn">3</div><div class="sl">En attente</div></div></div>
<div class="sci"><div class="si" style="background:var(--red-light)">{IC["warn"]}</div><div><div class="sn">2</div><div class="sl">Urgents</div></div></div>
<div class="sci"><div class="si" style="background:var(--blue-light)">{IC["info"]}</div><div><div class="sn">12</div><div class="sl">Total</div></div></div>
</div>
<div class="cd" style="padding:0 16px">
<div class="li"><div class="lic" style="background:var(--red-light)">{IC["trash"]}</div><div class="lin"><h4>Dechets · Pont de Bassam</h4><p>22/07/2026 · 14:30 · GPS auto</p></div><span class="cp r">Urgent</span></div>
<div class="li"><div class="lic" style="background:var(--orange-light)">{IC["water"]}</div><div class="lin"><h4>Eaux stagnantes · Marcory</h4><p>22/07/2026 · 10:15 · GPS auto</p></div><span class="cp o">Modere</span></div>
<div class="li"><div class="lic" style="background:var(--green-light)">{IC["trash"]}</div><div class="lin"><h4>Dechets · Bd Latrille</h4><p>21/07/2026 · 16:45 · GPS auto</p></div><span class="cp g">Traite</span></div>
<div class="li"><div class="lic" style="background:var(--red-light)">{IC["dust"]}</div><div class="lin"><h4>Poussieres · Rocade Marcory</h4><p>21/07/2026 · 09:20 · GPS manuel</p></div><span class="cp r">Urgent</span></div>
<div class="li"><div class="lic" style="background:var(--green-light)">{IC["trash"]}</div><div class="lin"><h4>Dechets · Marcory</h4><p>20/07/2026 · 11:00 · GPS auto</p></div><span class="cp g">Traite</span></div>
</div>
</div>
{navbar("Signalements")}
</div></div>''')

# 6. FILTRES
screens.append(f'''<div class="ph"><div class="nt"></div><div class="sc">
{sb()}
{appbar("Filtres","Affiner les signalements","doc",back=True)}
<div class="cn">
<div class="cd"><div class="ct">{IC["doc"]} Statut</div>
<div class="fl-row"><div class="fl-chip act">Tous</div><div class="fl-chip">En attente</div><div class="fl-chip">En cours</div><div class="fl-chip">Traite</div><div class="fl-chip">Rejete</div></div>
</div>
<div class="cd"><div class="ct">{IC["warn"]} Criticite</div>
<div class="fl-row"><div class="fl-chip act">Toutes</div><div class="fl-chip">Faible</div><div class="fl-chip">Modere</div><div class="fl-chip">Eleve</div></div>
</div>
<div class="cd"><div class="ct">{IC["pin"]} Chantier</div>
<div class="fl-row"><div class="fl-chip act">Tous</div><div class="fl-chip">Pont de Bassam</div><div class="fl-chip">Bd Latrille</div><div class="fl-chip">Rocade Marcory</div></div>
</div>
<div class="cd"><div class="ct">{IC["chart"]} Periode</div>
<div class="fl-row"><div class="fl-chip act">7 jours</div><div class="fl-chip">30 jours</div><div class="fl-chip">3 mois</div><div class="fl-chip">Personnalisé</div></div>
</div>
<div class="cd"><div class="ct">{IC["trash"]} Type de nuisance</div>
<div class="fl-row"><div class="fl-chip act">Tous</div><div class="fl-chip">Dechets</div><div class="fl-chip">Eaux</div><div class="fl-chip">Poussieres</div><div class="fl-chip">Bruit</div><div class="fl-chip">Vegetation</div></div>
</div>
<button class="bt bt-p">{IC["check"]} Appliquer les filtres</button>
</div></div></div>''')

# 7. DETAIL SIGNALEMENT
screens.append(f'''<div class="ph"><div class="nt"></div><div class="sc">
{sb()}
{appbar("Detail du signalement","SIG-2026-0042","doc",back=True,notif=True)}
<div class="cn">
<div class="dt-card">
<div class="dt-img">{IC["cam"]}</div>
<div class="dt-body">
<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">
<h3 style="font-size:15px;font-weight:700;color:var(--gray-800)">Dechets · Pont de Bassam</h3>
<span class="cp r">Urgent</span>
</div>
<div class="dt-row"><span class="dk">Date</span><span class="dv">22/07/2026 · 14:30</span></div>
<div class="dt-row"><span class="dk">Type</span><span class="dv">Dechets de chantier</span></div>
<div class="dt-row"><span class="dk">Chantier</span><span class="dv">Pont de Bassam · Lot 1</span></div>
<div class="dt-row"><span class="dk">GPS</span><span class="dv">5.3600 N, 4.0083 W</span></div>
<div class="dt-row"><span class="dk">Criticite IA</span><span class="dv" style="color:var(--orange)">Moderee (87%)</span></div>
<div class="dt-row"><span class="dk">Criticite agent</span><span class="dv" style="color:var(--red)">Elevee (confirmée)</span></div>
<div class="dt-row"><span class="dk">Statut</span><span class="dv" style="color:var(--red)">En attente</span></div>
</div>
</div>
<div class="cd">
<div class="ct">{IC["brain"]} Diagnostic IA</div>
<p style="font-size:12px;color:var(--gray-600);line-height:1.5">3 objets detectes : plastique, metal, dechets organiques. Confiance globale : 87%. Classe en criticite moderee par le modele MobileNetV2.</p>
</div>
<div class="cd">
<div class="ct">{IC["info"]} Description agent</div>
<p style="font-size:12px;color:var(--gray-600);line-height:1.5">Accumulation importante de dechets pres du pont, coté Bassam. Risque de pollution de la lagune.</p>
</div>
<div class="cd">
<div class="ct">{IC["edit"]} Action corrective</div>
<div class="ig" style="margin-top:8px"><label class="il">Action envisagee</label><input class="ip" type="text" placeholder="Ex : Evacuation des dechets par le prestataire"></div>
<div class="ig"><label class="il">Echeance</label><input class="ip" type="date" value="2026-07-25"></div>
</div>
<button class="bt bt-p" style="margin-bottom:8px">{IC["check"]} Marquer comme traite</button>
<button class="bt bt-s" style="margin-bottom:8px">{IC["back"]} Retourner a l'agent (incomplet)</button>
<div class="ig"><label class="il">Motif du retour (si incomplet)</label><input class="ip" type="text" placeholder="Ex : Photo floue, GPS manquant..."></div>
</div></div></div>''')

# 7b. DETAIL SIGNALEMENT - SANS IA (Eaux stagnantes)
screens.append(f'''<div class="ph"><div class="nt"></div><div class="sc">
{sb()}
{appbar("Detail du signalement","SIG-2026-0043","water",back=True,notif=True)}
<div class="cn">
<div class="dt-card">
<div class="dt-img">{IC["cam"]}</div>
<div class="dt-body">
<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">
<h3 style="font-size:15px;font-weight:700;color:var(--gray-800)">Eaux stagnantes · Marcory</h3>
<span class="cp o">Modere</span>
</div>
<div class="dt-row"><span class="dk">Date</span><span class="dv">22/07/2026 · 10:15</span></div>
<div class="dt-row"><span class="dk">Type</span><span class="dv">Eaux stagnantes</span></div>
<div class="dt-row"><span class="dk">Chantier</span><span class="dv">Rocade Marcory · Lot 2</span></div>
<div class="dt-row"><span class="dk">GPS</span><span class="dv">5.3500 N, 4.0183 W</span></div>
<div class="dt-row"><span class="dk">Criticite</span><span class="dv" style="color:var(--orange)">Moderee (evaluation agent)</span></div>
<div class="dt-row"><span class="dk">Statut</span><span class="dv" style="color:var(--orange)">En cours</span></div>
</div>
</div>
<div class="cd">
<div class="ct">{IC["info"]} Description agent</div>
<p style="font-size:12px;color:var(--gray-600);line-height:1.5">Stagnation d'eau apres les pluies recentes. Risque de proliferation de moustiques sur le chantier.</p>
</div>
<div class="cd">
<div class="ct">{IC["edit"]} Action corrective</div>
<div class="ig" style="margin-top:8px"><label class="il">Action envisagee</label><input class="ip" type="text" placeholder="Ex : Pompage et drainage"></div>
<div class="ig"><label class="il">Echeance</label><input class="ip" type="date" value="2026-07-28"></div>
</div>
<button class="bt bt-p" style="margin-bottom:8px">{IC["check"]} Marquer comme traite</button>
<button class="bt bt-s" style="margin-bottom:8px">{IC["back"]} Retourner a l'agent (incomplet)</button>
<div class="ig"><label class="il">Motif du retour (si incomplet)</label><input class="ip" type="text" placeholder="Ex : Description insuffisante..."></div>
</div></div></div>''')

# 7c. ETAT VIDE - AUCUN SIGNALEMENT
screens.append(f'''<div class="ph"><div class="nt"></div><div class="sc">
{sb()}
{appbar("Signalements","0 au total","doc",notif=True)}
<div class="cn" style="display:flex;flex-direction:column;align-items:center;justify-content:center;flex:1;text-align:center">
<div style="width:72px;height:72px;border-radius:24px;background:var(--gray-100);display:flex;align-items:center;justify-content:center;margin-bottom:16px">{IC["doc"]}</div>
<h3 style="font-size:16px;font-weight:700;color:var(--gray-800)">Aucun signalement</h3>
<p style="font-size:12px;color:var(--gray-600);margin-top:6px;line-height:1.5">Aucun signalement ne correspond<br>a vos criteres de filtrage.</p>
<button class="bt bt-p" style="margin-top:20px;width:auto;padding:12px 24px">{IC["plus"]} Creer un signalement</button>
</div>
{navbar("Signalements")}
</div></div></div>''')

# 7d. CHANGER MOT DE PASSE (depuis parametres)
screens.append(f'''<div class="ph"><div class="nt"></div><div class="sc">
{sb()}
{appbar("Changer mot de passe","Modifier votre mot de passe","lock",back=True)}
<div class="cn">
<div class="cd" style="text-align:center;padding:20px">
<div style="width:56px;height:56px;border-radius:16px;background:var(--green-light);display:flex;align-items:center;justify-content:center;margin:0 auto 12px">
<svg viewBox="0 0 24 24" fill="var(--green)" width="28" height="28"><path d="M18 8h-1V6c0-2.76-2.24-5-5-5S7 3.24 7 6v2H6c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V10c0-1.1-.9-2-2-2zm-6 9c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2zm3.1-9H8.9V6c0-1.71 1.39-3.1 3.1-3.1 1.71 0 3.1 1.39 3.1 3.1v2z"/></svg>
</div>
<p style="font-size:12px;color:var(--gray-600);line-height:1.5">Saisissez votre mot de passe actuel puis choisissez un nouveau.</p>
</div>
<div class="ig"><label class="il">Mot de passe actuel</label><div class="pw-wrap"><input class="ip" type="password" placeholder="· · · · · · · ·" style="padding-right:44px"><div class="pw-toggle">{IC["eyeoff"]}</div></div></div>
<div class="ig"><label class="il">Nouveau mot de passe</label><div class="pw-wrap"><input class="ip" type="password" placeholder="Min. 8 caracteres" style="padding-right:44px"><div class="pw-toggle">{IC["eyeoff"]}</div></div><div class="hint"><b>8 caracteres min.</b> · 1 majuscule · 1 chiffre · 1 caractere special</div></div>
<div class="ig"><label class="il">Confirmer le mot de passe</label><div class="pw-wrap"><input class="ip" type="password" placeholder="Repeter" style="padding-right:44px"><div class="pw-toggle">{IC["eye"]}</div></div></div>
<button class="bt bt-p" style="margin-top:8px">{IC["check"]} Changer mon mot de passe</button>
</div></div></div>''')

# 8. STATISTIQUES
screens.append(f'''<div class="ph"><div class="nt"></div><div class="sc">
{sb()}
{appbar("Statistiques","Juillet 2026","chart")}
<div class="cn">
<div class="sg">
<div class="sci"><div class="si" style="background:var(--green-light)">{IC["doc"]}</div><div><div class="sn">12</div><div class="sl">Signalements</div></div></div>
<div class="sci"><div class="si" style="background:var(--orange-light)">{IC["check"]}</div><div><div class="sn">85%</div><div class="sl">Taux traitement</div></div></div>
</div>
<div class="cd"><div class="ct">{IC["chart"]} Repartition par nuisance</div>
<div class="br"><div class="bl"><span>Dechets de chantier</span><span>6 (50%)</span></div><div class="bt2"><div class="bf" style="width:50%;background:var(--green)"></div></div></div>
<div class="br"><div class="bl"><span>Eaux stagnantes</span><span>3 (25%)</span></div><div class="bt2"><div class="bf" style="width:25%;background:var(--blue)"></div></div></div>
<div class="br"><div class="bl"><span>Poussieres</span><span>2 (17%)</span></div><div class="bt2"><div class="bf" style="width:17%;background:var(--orange)"></div></div></div>
<div class="br"><div class="bl"><span>Bruit</span><span>1 (7%)</span></div><div class="bt2"><div class="bf" style="width:7%;background:#9C27B0"></div></div></div>
<div class="br"><div class="bl"><span>Degradation vegetation</span><span>1 (8%)</span></div><div class="bt2"><div class="bf" style="width:8%;background:#4CAF50"></div></div></div>
</div>
<div class="cd"><div class="ct">{IC["chart"]} Evolution mensuelle</div>
<div class="cbs">
<div class="cbc"><div class="cbb" style="height:35%;background:var(--green-light)"></div><span>Mai</span></div>
<div class="cbc"><div class="cbb" style="height:55%;background:var(--green)"></div><span>Juin</span></div>
<div class="cbc"><div class="cbb" style="height:80%;background:var(--green)"></div><span>Juil</span></div>
</div>
</div>
</div>
{navbar("Stats")}
</div></div>''')

# 9. ALERTES
screens.append(f'''<div class="ph"><div class="nt"></div><div class="sc">
{sb()}
{appbar("Alertes","3 nouvelles notifications","bell",back=True)}
<div class="cn">
<div class="al-item"><div class="al-icon" style="background:var(--red-light)">{IC["warn"]}</div><div class="al-info"><h4>Signalement urgent</h4><p>Dechets · Pont de Bassam · Criticite elevee</p></div><span class="al-time">Il y a 5 min</span></div>
<div class="al-item" style="background:var(--red-light);border-radius:12px;padding:12px;margin:0 -8px"><div class="al-icon" style="background:var(--red)">{IC["warn"]}</div><div class="al-info"><h4>Seuil depasse</h4><p>Indice qualite air · Rocade Marcory · PM2.5 &gt; 65</p></div><span class="al-time">Hier</span></div>
<div style="padding:0 16px;margin-top:8px"><button class="bt bt-p" style="width:auto;padding:10px 20px">{IC["check"]} Accuser reception</button></div>
<div class="al-item"><div class="al-icon" style="background:var(--orange-light)">{IC["sync"]}</div><div class="al-info"><h4>Synchronisation requise</h4><p>3 signalements en attente d'envoi</p></div><span class="al-time">Il y a 1h</span></div>
<div class="al-item"><div class="al-icon" style="background:var(--green-light)">{IC["check"]}</div><div class="al-info"><h4>Signalement traite</h4><p>Dechets · Bd Latrille · Traite par Expert HSE</p></div><span class="al-time">Il y a 3h</span></div>
<div class="al-item"><div class="al-icon" style="background:var(--blue-light)">{IC["info"]}</div><div class="al-info"><h4>Nouveau chantier assigne</h4><p>Rocade Marcory · Lot 2 · Vous etes assigne</p></div><span class="al-time">2 jours</span></div>
</div></div></div>''')

# 10. SYNCHRONISATION
screens.append(f'''<div class="ph"><div class="nt"></div><div class="sc">
{sb()}
{appbar("Synchronisation","3 signalements a envoyer","sync",back=True)}
<div class="cn">
<div class="cd" style="text-align:center;padding:24px">
<div style="width:64px;height:64px;border-radius:20px;background:var(--green-light);display:flex;align-items:center;justify-content:center;margin:0 auto 12px">{IC["sync"]}</div>
<h3 style="font-size:16px;font-weight:700;color:var(--gray-800)">Synchronisation en cours</h3>
<p style="font-size:12px;color:var(--gray-600);margin-top:4px">Envoi des donnees vers le serveur...</p>
<div class="pg" style="margin-top:16px"><div class="pf" style="width:67%"></div></div>
<p style="font-size:11px;color:var(--gray-600);margin-top:4px">2/3 envoyes</p>
</div>
<div class="cd">
<div class="ct">{IC["doc"]} File d'attente</div>
<div class="li"><div class="lic" style="background:var(--green-light)">{IC["check"]}</div><div class="lin"><h4>Dechets · Bd Latrille</h4><p>Envoye · SIG-2026-0041</p></div></div>
<div class="li"><div class="lic" style="background:var(--green-light)">{IC["check"]}</div><div class="lin"><h4>Eaux · Marcory</h4><p>Envoye · SIG-2026-0042</p></div></div>
<div class="li"><div class="lic" style="background:var(--orange-light)">{IC["sync"]}</div><div class="lin"><h4>Dechets · Pont Bassam</h4><p>Envoi en cours...</p></div></div>
</div>
</div></div></div>''')

# 11. PROFIL
screens.append(f'''<div class="ph"><div class="nt"></div><div class="sc">
{sb()}
{appbar("Mon profil","Responsable Environnement","user")}
<div class="cn" style="padding:0">
<div class="ph2"><div class="av">{IC["user"]}</div><h3>KONANBOUO Georges</h3><p>CC-PTUA · AGEROUTE</p><div style="margin-top:8px;display:flex;gap:6px;justify-content:center;flex-wrap:wrap"><span class="cp g">En ligne</span><span class="cp b">Resp. Environnement</span></div><p style="font-size:10px;color:var(--gray-400);margin-top:6px">Saisie terrain · Mobile</p></div>
<div class="cd" style="padding:0;margin:0 16px 12px">
<div class="mn"><div class="mm" style="background:var(--green-light)">{IC["mail"]}</div><div class="mt2"><h4>g.konanbouo@ageroute.ci</h4><p>Email professionnel</p></div><div class="ma">{IC["fwd"]}</div></div>
<div class="mn"><div class="mm" style="background:var(--blue-light)">{IC["phone"]}</div><div class="mt2"><h4>+225 07 00 00 00</h4><p>Telephone</p></div><div class="ma">{IC["fwd"]}</div></div>
<div class="mn"><div class="mm" style="background:var(--orange-light)">{IC["pin"]}</div><div class="mt2"><h4>Cellule Coordination PTUA</h4><p>Direction</p></div><div class="ma">{IC["fwd"]}</div></div>
</div>
<div class="cd" style="padding:0;margin:0 16px 12px">
<div class="mn"><div class="mm" style="background:var(--orange-light)">{IC["sync"]}</div><div class="mt2"><h4>Synchroniser</h4><p>3 signalements en attente</p></div><div class="ma">{IC["fwd"]}</div></div>
<div class="mn"><div class="mm" style="background:var(--gray-100)">{IC["gear"]}</div><div class="mt2"><h4>Parametres</h4><p>Preferences de l'application</p></div><div class="ma">{IC["fwd"]}</div></div>
<div class="mn"><div class="mm" style="background:var(--green-light)">{IC["lock"]}</div><div class="mt2"><h4>Changer mon mot de passe</h4><p>Modifier le mot de passe actuel</p></div><div class="ma">{IC["fwd"]}</div></div>
</div>
<div style="padding:0 16px"><button class="bt bt-r">{IC["logout"]} Se deconnecter</button></div>
</div>
{navbar("Profil")}
</div></div>''')

# 12. PARAMETRES
screens.append(f'''<div class="ph"><div class="nt"></div><div class="sc">
{sb()}
{appbar("Parametres","Preferences","gear",back=True)}
<div class="cn">
<div class="cd" style="padding:0 16px">
<div class="ct" style="padding-top:14px">{IC["cloud"]} Donnees</div>
<div class="tg"><div class="tg-info"><h4>Mode hors ligne</h4><p>Enregistrer sans connexion</p></div><div class="sw on"></div></div>
<div class="tg"><div class="tg-info"><h4>Synchronisation auto</h4><p>Envoyer des que connexion disponible</p></div><div class="sw on"></div></div>
<div class="tg"><div class="tg-info"><h4>Wifi uniquement</h4><p>Ne pas utiliser les donnees mobiles</p></div><div class="sw"></div></div>
</div>
<div class="cd" style="padding:0 16px">
<div class="ct" style="padding-top:14px">{IC["gps"]} Localisation</div>
<div class="tg"><div class="tg-info"><h4>GPS automatique</h4><p>Capturer les coordonnees a la saisie</p></div><div class="sw on"></div></div>
<div class="tg"><div class="tg-info"><h4>Haute precision</h4><p>Utiliser GPS + reseau</p></div><div class="sw on"></div></div>
</div>
<div class="cd" style="padding:0 16px">
<div class="ct" style="padding-top:14px">{IC["bell"]} Notifications</div>
<div class="tg"><div class="tg-info"><h4>Alertes urgentes</h4><p>Notifier pour criticite elevee</p></div><div class="sw on"></div></div>
<div class="tg"><div class="tg-info"><h4>Vibrer</h4><p>Vibration lors des alertes</p></div><div class="sw on"></div></div>
<div class="tg"><div class="tg-info"><h4>Son</h4><p>Son de notification</p></div><div class="sw"></div></div>
</div>
<div class="cd" style="padding:0 16px">
<div class="ct" style="padding-top:14px">{IC["info"]} A propos</div>
<div class="dt-row"><span class="dk">Version</span><span class="dv">1.0.0</span></div>
<div class="dt-row"><span class="dk">Build</span><span class="dv">2026.07.22</span></div>
<div class="dt-row"><span class="dk">Serveur</span><span class="dv">api.si-env.ageroute.ci</span></div>
</div>
</div></div></div>''')

# === ASSEMBLE FINAL HTML ===
html = f'''<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SI-ENV · App Mobile Complete</title>
<style>
{CSS}
</style>
</head>
<body>
<div class="tw"><h1>SI-ENV · Application Mobile</h1><p>23 ecrans complets · AGEROUTE / PTUA · Material Design 3</p></div>
{''.join(screens)}
</body></html>'''

out = r'C:\Users\DELL\CascadeProjects\si-env-maquettes\app_complete.html'
with open(out, 'w', encoding='utf-8') as f:
    f.write(html)
print(f'OK · {len(screens)} ecrans · {len(html)} chars · {out}')
