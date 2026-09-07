# Talking about this project

Not part of the tool. Notes for defending it in an interview — for BD / search &
evaluation, strategy, and healthcare investment conversations, where the question
is never "can you code" but "do you know what the output is for".

## The one-line version

> I built a reference database for drug targets. Give it a gene and it returns
> what has been tried against it grouped by mechanism, what stopped and the
> reason the sponsor gave, what the running trials are designed to show, and
> which well-evidenced diseases have nothing in the clinic — every number
> traceable to a public source, and no generated conclusions anywhere.

If they ask why, the honest answer is the strongest one: *I did competitive
landscape and pipeline mapping by hand during an equity research internship, and
the mechanical part of it — pull the assets, dedupe them, group them, read the
termination notices — is the same every time. So I automated that part and kept
the judgement.*

## The question you will get, and the answer

**"医药魔方 / Cortellis / Evaluate already does this."**

They do the retrieval, and they do it better — they have licensed data this tool
cannot touch. What they hand you is a list. Four things this does that a list
does not — lead with the second and the third:

1. **Groups by mechanism rather than counting.** Five antibodies against a receptor
   is one competitive situation if they all block the ligand and a different one if
   two deplete the cell.

2. **Separates science failures from business failures.** This is the real answer.
   A termination count is worse than useless — a large share of trials stop because
   funding ran out or a merger reshuffled the portfolio, and counting those as
   evidence against the target walks a team away from something that never failed.
   The tool classifies the sponsor's own `whyStopped` text and reports the split.

   *Have the BAFF-R case ready, because it is a real one and it makes the point in
   fifteen seconds:* Novartis stopped its Phase 2b in hidradenitis suppurativa
   saying the study "did not meet the target criteria for progression despite
   demonstrating efficacy versus placebo… no new safety signals were identified."
   Keyword matching reads the word "safety" and files that as a toxicity failure —
   which inverts the conclusion. The tool masks negated clauses, classifies it as a
   portfolio decision, and flags that it also matched efficacy so the analyst can
   overrule it. That is the difference between a search tool and an analysis tool.

3. **Answers the BD question, which no database answers.** Every target
   database tells you what exists. It does not tell you which of those assets
   you could get. The Licensing view derives that from data already on the
   page — a Phase 2 asset whose every trial has stopped is a shelved programme
   with human data; a sponsor running trials only in China has probably not
   placed its ex-China rights; a single-asset academic sponsor is looking for
   a partner — and shows the evidence for each so the analyst can overrule it.
   That is the first pass of a search-and-evaluation shortlist, automated.

4. **States its assumptions.** The density score prints its own weights. The
   whitespace section is labelled a screen, not a finding. Every memo has a "what
   this cannot see" section. If they push on the score, agree first — the bands are
   hand-calibrated and I say so in the memo and the docs — then point out that
   being able to recompute someone's number is the whole reason it is printed.

**"Where do the deal comparables come from?"**
Answer this one before they ask, because it is the honest limit. There is no
free, redistributable deal database, so that table is hand-curated with a
source URL on every row, and the tool renders it as empty rather than implying
there were no deals. What is automated around it is the part that can be: deals
are matched to the asset table by name, and priced by stage so you can see what
a Phase 2 on this mechanism has been worth.

One detail worth volunteering, because it is the kind of thing that gets caught:
**acquisitions are excluded from the medians.** An acquisition price buys the
company, not the asset. On the BAFF/APRIL axis, averaging the Vertex–Alpine and
Novartis–Chinook prices against the Vor–RemeGen licence turns a Phase 3 median
of $125m into $1.66bn — a different claim about the field entirely. The rows are
still in the table, labelled, because they answer the other question: what a
buyer paid for the whole programme.

## Three more you should expect

**"How do you know it isn't double-counting?"**
Reconciliation is the part I spent the most time on. Identity resolves on ChEMBL ID
where available, otherwise a normalised key over all synonyms with dose and
formulation stripped. Phase takes the maximum across sources because ChEMBL's
`max_phase` lags behind the registry. Sponsor comes from the industry lead sponsor
of the highest-phase trial, and academic-only programmes are flagged rather than
counted as competitors.

**"Where does the LLM sit?"**
Deliberately at the edge. Rules classify first; the model gets only the residue,
is constrained to the same controlled vocabulary, has its low-confidence answers
discarded, and every row it touches is tagged. The tool produces a complete memo
with no model at all. An analysis whose numbers change when you swap the model is
not an analysis — and that is a position I would defend in any AI-in-pharma
conversation, not just about this tool.

**"Why is there no AI in the part that writes?"**
Worth volunteering, because it is the opposite of what an interviewer expects
in 2026. The header paragraph on every target is curated UniProt annotation
assembled by rule, with the curator's own PubMed citations attached — not a
model summary. A paragraph that comes out different every time it is generated
is not an annotation, and that block is the one a reader is most likely to
quote onward. The same argument as the mechanism classifier, one layer up: the
model gets the residue, never the load-bearing text.

**"What's wrong with it?"**
Answer immediately and specifically; hedging here costs more than the flaw does.
Only ClinicalTrials.gov is swept, so China- and Japan-only registrations are
under-represented — CTIS, ChiCTR and jRCT are the obvious next sources and I know
that is the biggest gap. Preclinical programmes are invisible. Disease-name
matching is stemmed token overlap, not real EFO mapping. The crowding bands are a
convention calibrated by hand against a handful of targets, not a measurement.

## Choosing a demo target

Run it live in front of them if you can. Two or three targets, one of which you can
defend three layers deep:

- **BAFF-R / TNFRSF13C** — your own. You can go from the memo's mechanism split
  down to why an afucosylated antibody depletes rather than blocks, and why common
  variable immunodeficiency surfacing as top whitespace on genetic evidence is
  biologically sensible. Nobody can follow you there, and the point of a demo is
  showing where your judgement exceeds the tool's.
- **A target relevant to their pipeline.** Look up what they are working on and run
  it beforehand. This is the one that gets remembered.
- **A crowded target** to show the density verdict changing — the contrast is what
  makes the score legible.

Worth having ready: the tool correctly *excludes* belimumab, atacicept, telitacicept
and povetacicept from a BAFF-R landscape. They are all on the BAFF/APRIL axis but
bind the ligands or TACI, not the receptor. A keyword search sweeps them in; a
target-resolved pipeline does not. It is a small thing that shows you know the
difference between searching for a string and searching for a target.

## For the CV

One line under the project, not a paragraph. Something like:

> **target-landscape** — open-source tool generating competitive landscape memos for
> drug targets from Open Targets, ChEMBL and ClinicalTrials.gov; classifies assets
> by mechanism, separates science-driven from business-driven trial terminations,
> and derives which programmes may be available to license. Python + FastAPI,
> 198 tests. `github.com/<you>/target-landscape`

Claim the analytical design, not the engineering scale.

---

## 中文要点

面试里最容易被问的一句是"医药魔方不是已经有了吗"。**不要辩护检索能力**——直接承认他们的数据更全，然后把话题转到判断层：

- **按机制分层而不是罗列**：同一个靶点上五个抗体，全是阻断型和其中两个是耗竭型，是完全不同的竞争格局。
- **区分"科学失败"和"商业失败"**（这是主打）：终止试验的数量本身没有信息量，很多是资金断了或并购后砍管线，把这些算成靶点的负面证据，会让团队错过一个其实没失败过的靶点。工具解析申办方自己写的 `whyStopped` 原文并分类。
  - 拿 BAFF-R 那个真实案例讲：诺华的 HS 二期 b 终止说明写的是"虽然相对安慰剂显示出疗效，但未达到推进标准……未发现新的安全性信号"。关键词匹配会抓到 "safety" 判成毒性失败，结论正好反了。工具会屏蔽被否定的从句、判为组合决策，并标注"同时命中 efficacy"让分析师自己推翻。
- **回答 BD 真正在问的问题**：所有靶点数据库都告诉你"有什么"，没有一个告诉你"哪些拿得到"。Licensing 视图从页面上已有的数据推导：二期做完但所有试验都停了 = 有人体数据的搁置资产（典型的 in-license 标的）；只在中国做试验的申办方，海外权益大概率没出手；单一资产的学术申办方本来就在找合作方。每条信号都附上触发它的证据，分析师可以直接推翻。这是把 S&E 尽调的第一遍筛选自动化了。
- **把假设摆在明面上**：拥挤度评分把自己的权重打印在页脚，whitespace 明确标为"待人工验证的筛选"而不是结论，每份 memo 都有"这份分析看不到什么"一节。
- **交易可比诚实交代来源**：没有免费可再分发的交易数据库，所以那张表是手工维护、每行必须附来源链接的；没有数据时页面显示"空"而不是暗示"没有交易发生过"。能自动化的部分是：交易按名称匹配到资产表，并按阶段算中位首付款。

被问缺陷时**立刻具体地答**：只扫了 ClinicalTrials.gov，中日本土注册的试验覆盖不足（下一步接 CTIS、ChiCTR、jRCT）；临床前看不到；疾病名匹配是词干重叠不是真正的 EFO 映射；拥挤度分档是人工标定的约定不是测量。承认得越快越具体，越像做过这件事的人。

演示优先选 **BAFF-R**——你能从 memo 的机制分层一路讲到去岩藻糖化抗体为什么是耗竭而不是阻断、以及 CVID 凭遗传学证据排在 whitespace 第一位在生物学上为什么成立。演示的意义是展示你的判断力超过工具本身。

---

## 新增的一层：从"信息"到"判断"（早期投资视角）

前面那些回答的是 BD 的问题。这一层回答的是**天使/VC 看一个早期项目时的问题**，也是整个工具最容易讲出差异化的部分。

靶点页开头是靶点本身的基本情况（UniProt 策展的功能、定位、结构域、在研情况），接着是六个问题，每一个都点得回下面对应的视图。这六个问题的顺序就是一个种子轮尽调的顺序，但页面只给记录里有什么，不替读者下结论：

1. **这个靶点是真的吗** — 有没有已上市药物；有没有人试过并失败。
2. **前人死在哪** — 这一条是资产数据库结构上答不了的：**失败的项目会从在研资产表里消失**。一个靶点上三个三期因无效终止，新公司来讲故事时，那张表是干净的。
3. **窗口还开着吗** — 按期别加权，不是数个数。
4. **在跑的试验能不能settle问题** — 见下。
5. **什么时候 settle** — 下一个可解读的读出，带日期。
6. **还剩什么没做** — 物理上可行但没人碰的模态，或者没人做的适应症。

### 三个可以拿来讲的技术判断

**(1) 试验不是可互换的计数单位。** 十四个二期听上去像一个被验证过的、拥挤的机制。如果其中十一个是单臂、开放标签、主要终点是受体占有率，那这个机制**根本没被测试过**，而且花掉的钱不会给出答案。关键在于：这件事在试验读出之前好几年就能知道，因为设计和主要终点是**预先注册**的。工具把每个主要终点分类（硬终点/公认替代终点/量表/生物标志物/PK/安全性），再结合随机化、盲法、入组数，给出"这个试验成功了能支持什么结论"。

  - 一句可以直接说的话：*"单臂开放标签的 PD 终点二期，无论结果多漂亮，在结构上都不可能证明疗效。这不是我的判断，这是设计决定的，而设计是公开的。"*

**(2) 没登记设计 ≠ 没有对照。** 这是我们踩过的坑：如果把设计字段缺失的试验算成"非对照"，就把**注册库的数据缺口**变成了**关于靶点的结论**。和把"未说明终止原因"读成"没有原因"是同一类错误。现在页面会直说这是记录缺口。

**(3) 模态对靶点提出什么要求。** ADC 不只需要表面表达，还需要**结合后内化**——一个特异性极好但不内化的抗原，是个死的 ADC 靶点。分子胶需要靶点在细胞内，但**不需要有功能性活性口袋**，这正是它能碰那些"不可成药"支架蛋白的原因。这类要求稳定、公开、行业内人尽皆知，**但没有任何免费数据库里有**。工具只自动检查其中最硬的一条（亚细胞定位），其余明确写出来交给人判断。
  - 而且：**定位未知时返回"无法判断"，绝不返回"可行"**。跟人说抗体能够到一个谁都没定位过的蛋白，是这一节唯一会真正让人赔钱的错误。

### 抬头为什么是一段文字，不是一张图

投资人做研报习惯放机制图，科学家看靶点第一眼也找图。但页面顶上那个位置真正要回答的问题是"**这个蛋白是什么**"——对一个没见过的靶点，这句话不说清楚，下面所有的竞争格局都读不出意思。图回答不了这个问题，一段话可以。

所以抬头是 100–200 字的策展注释，来自 UniProt/Swiss-Prot：
- **是人写的，不是模型写的**。Swiss-Prot 的注释是策展员读原始文献写的，每一条后面挂着他引用的 PubMed 记录，页面把这些引用做成上标链接。整块没有一个字是生成的，同一个靶点在任何机器上、有没有网，出来的段落都一样。
- **四类注释回答四个不同的问题**：FUNCTION 它做什么；SUBUNIT 它跟谁结合（决定了阻断型抗体有没有东西可阻断）；DOMAIN 结构域架构（小分子和降解剂要抓的把手）；DISEASE 人类遗传学已经把它指向哪里。
- **CC BY 4.0**，可以直接展示和引用——这一点比综述摘要干净，摘要在出版商手里。

如果被追问"为什么不用 LLM 写这段"：**一段每次生成都不一样的文字不是注释，是装饰**。而且这是整个页面上读者最可能直接引用出去的一块，它必须能溯源到具体的人和具体的文献。

### 机制图为什么是生成的，以及为什么挪走了

手画图撑不住"28,000 个靶点都要能用"这个要求。所以图是从三个数据字段生成的：蛋白在哪、属于哪个家族、资产表里实际存在哪些机制类别。

差别在于：**教科书的图画的是生物学，这张图画的是叠在生物学上的竞争格局**——箭头粗细是该路线走到的最高期别。拥挤的靶点上箭头挤成一团，空白的靶点画面是空的。这是这个工具传达 whitespace 最快的方式。

**它现在在 Mechanisms 标签页里，不在页面顶部。**理由值得讲，因为它是个设计判断：这张图画的是竞争结构，不是通路。放在抬头位置，读者会当通路图读——**一张诱导误读的图，比没有图更糟**。抬头位置留给它真正欠读者的东西：这个蛋白是什么。

### 为什么整个网站不给结论

这是最容易被追问、也最值得讲的一个设计决定。早期版本每个靶点页顶上有一句自动生成的判断（"已在人体验证且尚不拥挤"之类）。删掉了，理由是：**能查的 28,000 个靶点里，大多数是全新的或者数据很薄，而一个留了"结论"这个槽位的模板，不管记录支不支持都会把它填上**。那句话读起来像权威，但工具并没有挣到这个权威。

现在页面给的是：六个问题、六个来自下方表格的数字或日期，每个都标明出处和它**不能**说明什么。判断留给读者。

一句可以直接说的话：*"这不是一份自动生成的研报。研报的价值在于分析师的判断，而判断不能自动化——能自动化的是把判断需要的证据摆齐、并且诚实标注哪里是缺口。"*

### 被问到"你怎么控制信息过载"

直接说这条设计原则：**引擎可以厚，页面必须薄。**

- 结论有两个位置：抬头右侧一行 verdict（一句话，不折叠，字号压得很小），六行本体在页面底部证据之下，中间用一个"The six lines ↓"的锚点连起来。只想要答案的人一眼拿到，想验证的人往下走。
- 页面从上到下是三段：**它是什么**（一段策展注释）→ **它身上在发生什么**（八个标签页，页面重心）→ **这加起来说明什么**（六行总结）。六行原来在顶上，挪到了底部：结论印在证据前面，等于要求读者先信了再看，而每一行仍然可以点回它上面对应的那个视图。
- 首屏没有统计数字方块——原来有十个，删掉了。十个没有结论的数字，正是这个页面要避免的东西。
- 每一节 = 一句判断 + 最多三条证据，其余折叠。
- 原始数据不搬运，出站链接到 Open Targets / ClinicalTrials.gov / Europe PMC。他们的表做得比我好，做二手数据库没有意义。
- 算得出来但说不出结论的东西，不给它 UI。
