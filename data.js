const disciplines = [
  { id: 'core', number: '01', title: '核心人物', en: 'Characters', desc: '身份、关系与成长线', icon: '♢', tone: 'cyan', count: 12 },
  { id: 'org', number: '02', title: '组织与阵营', en: 'Factions', desc: '黑衣组织、FBI、公安与侦探', icon: '◈', tone: 'red', count: 9 },
  { id: 'story', number: '03', title: '故事主线', en: 'Story Arcs', desc: '从缩小事件到组织决战', icon: '⌁', tone: 'gold', count: 11 },
  { id: 'cases', number: '04', title: '案件与诡计', en: 'Casecraft', desc: '密室、诡计、证据与推理', icon: '⊙', tone: 'violet', count: 14 },
  { id: 'gadgets', number: '05', title: '道具与技术', en: 'Gadgets', desc: '阿笠博士、追踪与伪装', icon: '⌘', tone: 'blue', count: 13 },
  { id: 'movies', number: '06', title: '剧场版宇宙', en: 'Movies', desc: '独立冒险与高能舞台', icon: '▣', tone: 'orange', count: 10 },
  { id: 'world', number: '07', title: '地点与文化', en: 'Worldbuilding', desc: '米花町、学校与现实取景', icon: '⌂', tone: 'green', count: 8 },
  { id: 'meta', number: '08', title: '作品与作者', en: 'Meta', desc: '青山刚昌、连载与跨作品', icon: '✦', tone: 'pink', count: 7 }
];

const scenarios = [
  { id: 'start', icon: '◌', title: '我刚开始看', desc: '先建立世界观，避开关键剧透', count: '入门路径', level: 'beginner' },
  { id: 'organization', icon: '◈', title: '我想追黑衣组织', desc: '从 APTX4869 到多方卧底线', count: '主线入口', level: 'deep' },
  { id: 'relationship', icon: '∞', title: '我想看人物关系', desc: '新一、兰、灰原与对手们', count: '关系图谱', level: 'deep' },
  { id: 'casecraft', icon: '⊙', title: '我想研究案件', desc: '按诡计类型和推理结构浏览', count: '案件索引', level: 'beginner' },
  { id: 'movie', icon: '▣', title: '我只看剧场版', desc: '按年份、舞台和主题选择', count: '剧场版导览', level: 'beginner' },
  { id: 'full', icon: '⚠', title: '我准备好全剧透', desc: '打开完整主线与身份揭示', count: '全量档案', level: 'spoiler' }
];

const entries = [
  { id: 'conan', discipline: 'core', title: '江户川柯南', subtitle: '工藤新一的伪装身份', mark: 'C', color: 'cyan', level: 'beginner', tags: ['主角', '侦探', '身份'], intro: '外表是小学生，思考方式仍是高中生侦探。柯南的日常是用新的身份继续追查让自己变小的组织。', sections: [['一句话定位', '借住在毛利侦探事务所的神秘小学生，实际身份是工藤新一。'], ['能力与限制', '推理能力、观察力和行动力极强，但体格、身份暴露风险与信息不对称始终是限制。'], ['关联档案', '工藤新一、毛利兰、灰原哀、阿笠博士、黑衣组织'], ['阅读提示', '入门阶段先理解“身份隐藏”这个核心机制，再进入组织线。']], source: '原作基础设定 / Detective Conan World', spoiler: 1 },
  { id: 'shinichi', discipline: 'core', title: '工藤新一', subtitle: '平成的福尔摩斯', mark: 'K', color: 'blue', level: 'beginner', tags: ['主角', '新一线'], intro: '在多罗碧加乐园遭遇黑衣组织后身体缩小，工藤新一成为整个故事的真实起点。', sections: [['人物核心', '高中生侦探，崇拜福尔摩斯，习惯用证据拆解不可能。'], ['与柯南的关系', '柯南不是另一个人，而是新一为保护身边人而使用的长期身份。'], ['重要关系', '毛利兰是情感核心；服部平次是竞争与协作并存的侦探同伴。']], source: '原作基础设定', spoiler: 1 },
  { id: 'ran', discipline: 'core', title: '毛利兰', subtitle: '温柔与力量并存的日常支点', mark: 'R', color: 'pink', level: 'beginner', tags: ['人物', '空手道', '情感线'], intro: '毛利兰是毛利侦探的女儿，也是新一失踪后一直等待他回来的那个人。', sections: [['人物气质', '善良、敏锐、有很强的保护欲；她不是只等待答案的人，也经常主动行动。'], ['关系位置', '她连接毛利家、工藤家与柯南的日常生活，是身份秘密最危险也最温柔的见证者。']], source: '原作基础设定', spoiler: 1 },
  { id: 'haibara', discipline: 'core', title: '灰原哀', subtitle: '从雪莉到宫野志保', mark: 'H', color: 'violet', level: 'deep', tags: ['人物', '药物', '组织线'], intro: '曾经属于黑衣组织的研究员，在服下 APTX4869 后变小，以灰原哀的身份寻找逃离组织的方式。', sections: [['角色张力', '她知道组织的内部逻辑，也知道自己曾经参与了什么，因此她既是线索提供者，也是被追捕者。'], ['与柯南', '两人都拥有被迫改变的人生，但对风险、复原和牺牲的判断并不完全相同。'], ['阅读层级', '涉及组织、宫野家族和药物研究时，建议切换到“深入”或“全剧透”。']], source: '原作基础设定 / Detective Conan World', spoiler: 2 },
  { id: 'heiji', discipline: 'core', title: '服部平次', subtitle: '关西的高中生名侦探', mark: 'H', color: 'green', level: 'beginner', tags: ['人物', '侦探搭档'], intro: '与柯南在推理上互相较量，也逐步成为少数知道柯南真实身份并愿意守护秘密的人。', sections: [['侦探风格', '直觉强、行动快、擅长现场判断；与柯南的冷静拆解形成鲜明对照。'], ['关系网络', '远山和叶、柯南、工藤新一，以及关西警察系统。']], source: '原作基础设定', spoiler: 1 },
  { id: 'organization', discipline: 'org', title: '黑衣组织', subtitle: '主线中的暗面系统', mark: 'BO', color: 'red', level: 'deep', tags: ['组织', '主线', '代号'], intro: '以酒名为代号、长期进行秘密活动的犯罪组织。它不是单一反派，而是一套层级、情报和清除机制。', sections: [['观看方式', '把组织线看作情报战：谁知道什么、谁在伪装、谁在利用谁，比单个案件的凶手更重要。'], ['常见关键词', '琴酒、伏特加、贝尔摩德、雪莉、基尔、朗姆、APTX4869。'], ['剧透提示', '身份揭示较多，建议从“深入”模式开始。']], source: '原作主线 / Detective Conan World', spoiler: 2 },
  { id: 'fbi-public-security', discipline: 'org', title: 'FBI 与日本公安', subtitle: '正义阵营并不只有一种颜色', mark: '◆', color: 'blue', level: 'deep', tags: ['阵营', '赤井', '安室'], intro: 'FBI、日本公安和警方各自拥有任务、权限与情报盲区，多方行动让主线变成复杂的博弈。', sections: [['FBI', '以赤井秀一为核心的调查力量，与黑衣组织长期对抗。'], ['日本公安', '安室透等角色代表另一套国家安全与卧底逻辑。'], ['阅读重点', '观察同一事件在不同阵营眼中如何被重新解释。']], source: '原作主线', spoiler: 2 },
  { id: 'aptx4869', discipline: 'story', title: 'APTX4869', subtitle: '让主线开始转动的药物', mark: 'RX', color: 'violet', level: 'deep', tags: ['主线', '药物', '身份'], intro: '它让工藤新一和宫野志保的身体发生变化，也把两个原本不同的人生连接到一起。', sections: [['设定功能', '药物是身份变化的原因，也是组织研究、宫野家族和解药线的交汇点。'], ['阅读重点', '不要只把它理解为“变小药”，它更像一把打开组织世界的钥匙。']], source: '原作主线', spoiler: 2 },
  { id: 'tropical-land', discipline: 'story', title: '多罗碧加乐园事件', subtitle: '新一成为柯南的原点', mark: '01', color: 'gold', level: 'beginner', tags: ['起点', '主线'], intro: '工藤新一在游乐园目击可疑交易，遭到袭击并服下药物，醒来后发现身体已经缩小。', sections: [['叙事作用', '它同时完成世界观、身份秘密、组织威胁与兰的情感牵引。'], ['阅读提示', '这是所有主线阅读路径都应该记住的第一站。']], source: '原作第 1 话 / 动画第 1 集', spoiler: 1 },
  { id: 'sleeping-kogoro', discipline: 'story', title: '沉睡的小五郎', subtitle: '一套借来的侦探舞台', mark: '02', color: 'cyan', level: 'beginner', tags: ['机制', '毛利小五郎'], intro: '柯南用麻醉手表让毛利小五郎睡着，再用变声蝴蝶结传达推理，形成标志性破案机制。', sections: [['为什么重要', '它让一个小学生可以在不暴露身份的前提下影响案件，也让毛利事务所成为故事中心。'], ['机制边界', '道具不是万能答案，真正成立的仍然是证据链和推理。']], source: '原作早期案件 / Detective Conan World', spoiler: 1 },
  { id: 'voice-bowtie', discipline: 'gadgets', title: '变声蝴蝶结', subtitle: '隐藏身份的声音接口', mark: 'VB', color: 'cyan', level: 'beginner', tags: ['道具', '阿笠博士'], intro: '通过旋钮调整声音，柯南可以模仿他人的声线，是“沉睡的小五郎”机制的另一半。', sections: [['用途', '伪装、传话、制造现场发言者错觉。'], ['限制', '声音可以被伪装，推理链不能凭空出现。']], source: '道具资料 / Detective Conan World', spoiler: 1 },
  { id: 'tracking-glasses', discipline: 'gadgets', title: '追踪眼镜', subtitle: '把线索变成坐标', mark: 'TR', color: 'blue', level: 'beginner', tags: ['道具', '追踪'], intro: '眼镜接收发信器和少年侦探团徽章的信号，帮助柯南在城市空间里定位目标。', sections: [['叙事作用', '把传统侦探故事的“寻找”扩展为可视化的行动路线。'], ['关联道具', '发信器、侦探团徽章、手表型灯。']], source: '道具资料 / Detective Conan World', spoiler: 1 },
  { id: 'kick-shoes', discipline: 'gadgets', title: '增强脚力球鞋', subtitle: '小学生的物理外挂', mark: 'SH', color: 'orange', level: 'beginner', tags: ['道具', '阿笠博士'], intro: '通过电流和磁场刺激脚部肌肉，让柯南可以踢出远超体格的力量。', sections: [['使用场景', '足球、物体反弹、临时制止与现场行动。'], ['有趣细节', '它让“推理”不只发生在脑内，也变成空间、角度和时间的计算。']], source: '道具资料 / Detective Conan World', spoiler: 1 },
  { id: 'locked-room', discipline: 'cases', title: '密室诡计', subtitle: '门锁上之后，问题才开始', mark: 'L', color: 'gold', level: 'beginner', tags: ['案件类型', '诡计'], intro: '柯南案件常把“谁能进入现场”改写成“现场看起来为什么像密室”。', sections: [['阅读方法', '先列出密室成立条件，再逐项检查时间、钥匙、窗户、尸体状态与目击证词。'], ['观察点', '密室不是答案，它通常是凶手制造的第一层叙事。']], source: '案件结构整理', spoiler: 1 },
  { id: 'identity-trick', discipline: 'cases', title: '身份与伪装', subtitle: '看到的人未必是那个人', mark: 'ID', color: 'pink', level: 'deep', tags: ['案件类型', '身份'], intro: '变装、替身、假名和声音伪装构成作品中最稳定的一类谜题。', sections: [['阅读方法', '将“外貌”“声音”“行动动机”“可验证记录”分开判断。'], ['主线呼应', '案件里的身份诡计，经常与黑衣组织主线形成互文。']], source: '案件结构整理', spoiler: 2 },
  { id: 'movie-06', discipline: 'movies', title: '贝克街的亡灵', subtitle: '虚拟伦敦与现实选择', mark: '06', color: 'violet', level: 'beginner', tags: ['剧场版', '舞台'], intro: '以虚拟现实和福尔摩斯世界为舞台，讨论游戏、淘汰与孩子们的选择。', sections: [['观影入口', '适合喜欢推理舞台、群像协作和现实议题的观众。'], ['边界', '剧场版通常拥有独立冒险节奏，不应自动当作漫画主线事实。']], source: '剧场版导览', spoiler: 1 },
  { id: 'movie-13', discipline: 'movies', title: '漆黑的追踪者', subtitle: '组织线与剧场版的交界', mark: '13', color: 'red', level: 'deep', tags: ['剧场版', '黑衣组织'], intro: '把黑衣组织的压迫感带入剧场版结构，适合已经熟悉核心成员的观众。', sections: [['观看建议', '先了解组织成员代号，再看剧场版中的追踪与反追踪。']], source: '剧场版导览', spoiler: 2 },
  { id: 'beika', discipline: 'world', title: '米花町', subtitle: '日常生活的高密度案件场', mark: 'B', color: 'green', level: 'beginner', tags: ['地点', '城市'], intro: '学校、事务所、餐厅、车站、别墅和街区共同构成柯南的日常地理。', sections: [['空间特点', '案件发生频率极高，但地点变化也让作品拥有旅行、校园与都市生活的不同气质。']], source: '作品场景整理', spoiler: 1 },
  { id: 'aoyama', discipline: 'meta', title: '青山刚昌', subtitle: '把推理、动作与日常并置', mark: '73', color: 'gold', level: 'beginner', tags: ['作者', '作品'], intro: '作品的核心创作者。柯南也与《魔术快斗》等作品共享角色与创作回声。', sections: [['创作观察', '案件构思、角色关系、道具和跨作品人物共同构成持续扩张的世界。']], source: '作者公开资料 / 官方作品信息', spoiler: 1 }
];

const timeline = [
  { year: '1994', title: '缩小事件', desc: '工藤新一在游乐园遭遇黑衣组织，故事的身份秘密与追查主线同时启动。', level: 1 },
  { year: '早期', title: '毛利事务所与少年侦探团', desc: '柯南在日常案件中建立“沉睡的小五郎”机制，也逐渐拥有自己的伙伴网络。', level: 1 },
  { year: '组织线', title: '灰原哀加入', desc: '药物研究与组织威胁不再是远处的传闻，而成为柯南身边人的现实危险。', level: 2 },
  { year: '中段', title: 'FBI、公安与卧底', desc: '主线进入多方情报战，身份、伪装和阵营边界变得越来越复杂。', level: 2 },
  { year: '后段', title: '朗姆与组织核心', desc: '更深层的组织结构和长期伏笔开始被逐步揭开。', level: 3 },
  { year: '现在', title: '真相仍在推进', desc: '漫画与动画仍在更新，知识库将主线与独立案件、动画原创和剧场版分开记录。', level: 1 }
];

const relations = [
  ['江户川柯南', '工藤新一', '真实身份'], ['江户川柯南', '毛利兰', '守护与隐瞒'], ['江户川柯南', '灰原哀', '药物与共犯'], ['江户川柯南', '服部平次', '侦探同盟'], ['灰原哀', '黑衣组织', '逃离与追捕'], ['赤井秀一', 'FBI / 日本公安', '阵营协作'], ['安室透', '黑衣组织', '卧底关系'], ['怪盗基德', '江户川柯南', '镜像对手']
];

const glossary = [
  ['APTX4869', '组织研发的药物；主线身份变化和解药研究的核心关键词。'],
  ['红与黑', '多方阵营、身份判断与组织线交汇的长期叙事区域。'],
  ['沉睡的小五郎', '柯南借助道具隐藏身份并完成推理的经典机制。'],
  ['新兰', '工藤新一与毛利兰关系线的粉丝称呼。'],
  ['柯哀', '江户川柯南与灰原哀关系线的粉丝称呼。'],
  ['剧场版', '通常独立成篇、动作规模更大的电影系列，需与漫画主线区分。']
];
