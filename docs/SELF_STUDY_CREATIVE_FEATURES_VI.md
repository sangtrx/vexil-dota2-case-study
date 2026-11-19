# Tự học để bảo vệ toàn bộ bài Vexil, kể cả các thử nghiệm sáng tạo

**Hướng dẫn tiếng Việt, dành cho ứng viên | 18/11/2026 | Không phải tài liệu gửi nhà tuyển dụng.**

Mục tiêu: có thể mở đúng notebook, giải thích từng bước, hiểu ý nghĩa kinh tế/gameplay của feature, tự tính metric, chỉ ra khi nào kết luận không đáng tin, và trung thực về AI assistance. Kết quả thật lấy từ `REPORT.pdf`, `docs/CREATIVE_FEATURE_EXPERIMENT_ATLAS.md` và source readouts; ví dụ dùng chữ **giả định** không phải kết quả thật.

## 1. Hiểu bài toán theo ngôn ngữ đời thường

Dota 2 có đội **Radiant** và **Dire**, mỗi đội 5 người. Người chơi kiếm vàng (gold), điểm kinh nghiệm (XP), mua item, kiểm soát công trình (tower, barracks), chiếm Roshan/Aegis, giao tranh và cuối cùng một bên thắng.

Vexil muốn, **tại phút t** của một trận chuyên nghiệp, dự báo `p = P(Radiant thắng | các thông tin thực sự biết được đến t)`. Không phải dự đoán ai thắng bằng 0/1; đó là dự báo **xác suất** 0–1. Dự báo p=0.7 không phải Radiant chắc thắng; trong nhiều trạng thái được dự báo 0.7, tỷ lệ Radiant thắng cần tiệm cận 70% nếu calibration tốt.

Một trận 40 phút có nhiều hàng `(match_id, minute, features, radiant_win)`. Label `radiant_win` bằng 1 hoặc 0 là kết quả **cuối trận**; các minute rows cùng trận mang cùng nhãn. Do đó 18.292 hàng dự báo không có nghĩa 18.292 trận độc lập. Đây là bẫy lớn nhất của bài.

**Số liệu thật:** 500 trận OpenDota chuyên nghiệp trong 21–26/03/2026, 250 trận mỗi phía của patch change; TRAIN 291 trận/10.675 minute rows, VALIDATION 103/3.781, TEST 106/3.836; tất cả 18.292 hàng hợp lệ. Hàng phút t phải thỏa `60*t < match.duration`. Ví dụ **giả định**: trận dài đúng 2.400 giây thì phút 40 là terminal và không còn cơ hội forecast; phút 39 vẫn hợp lệ.

## 2. Feature, label, dataset, fit và predict

**Feature**: biến đầu vào được biết trước thời điểm dự báo. `gold_k = (Radiant gold - Dire gold)/1000`, `minute10=t/10`. **Label**: `radiant_win` cuối trận.

**Model training / fit**: từ các trận cũ đã kết thúc, học hệ số sao cho dự báo xác suất gần kết quả. **Inference**: với một trận mới, tính feature ở phút t rồi gọi `predict_proba` để tạo p. **Evaluation**: đo loss trên các trận chưa dùng để fit. **Overfitting**: mô hình học nhiễu của trận cũ thay vì quan hệ bền.

Ví dụ **giả định**: phút 20 Radiant hơn 3.000 gold; mô hình trả p=0.72. Không được đọc phút 30, item tương lai, hay radiant_win khi tạo feature ở phút 20.

## 3. Logistic regression: phải tự đọc được công thức

M0 tính `z=b0+b1*gold_k`, `p=1/(1+exp(-z))`. Sigmoid biến điểm thực thành xác suất 0–1. M1 thêm `minute10` và interaction `gold_x_time=gold_k*ln(1+t/10)`. Ý tưởng: một lợi thế vàng giống nhau có thể mang nghĩa khác nhau ở phút 10 và phút 35. **Ý nghĩa dự báo** khác **quan hệ nhân quả**: mô hình không chứng minh rằng “kéo dài thời gian sẽ gây ra thay đổi cơ hội thắng”.

Notebook gốc có bốn model:
- **M0**: gold only, bắt buộc làm baseline; validation LL 0.5325.
- **M1**: gold + time + interaction; validation LL 0.5197, tốt nhất trong M0–M3.
- **M2**: M1 + XP, recent gold/XP movement; validation LL 0.5224.
- **M3**: M2 + tower, barracks, Roshan, kills theo event timestamp; validation LL 0.5282.

Pipeline là `SimpleImputer(median)` → `StandardScaler` → `LogisticRegression(C=1, max_iter=1000)`. Imputer xử lý dữ liệu trống bằng median TRAIN; scaler dùng mean/std **học từ TRAIN**; logistic C=1 có L2 regularization giúp giảm cực đoan hệ số. Không fit scaler trên VAL/TEST. `fit` huấn luyện, `predict_proba` chỉ dự báo.

## 4. Feature engineering: tại sao phải “sáng tạo” thay vì chỉ lấy raw gold?

Feature engineering nghĩa là biến raw events thành tín hiệu kiểm chứng được theo phút. Hãy nghĩ theo **giả thuyết về cơ chế thắng**, không nghĩ theo số cột.

**Nhóm thời gian**: `minute10`, nonlinear time, spline, tương tác gold×time. Hỏi: +3k gold ở phút 10 và 30 có hàm ý khác không? Rủi ro: 20 cách biến đổi một cùng tín hiệu có thể là 20 phép thử trên nhãn đã xem.

**Nhóm biến động gold**: tốc độ thay đổi 1/3/5/10 phút, acceleration, volatility, range, retreat/drawdown, efficiency, số lần đổi dấu, thời gian từ đỉnh. Cùng +3k hiện tại, một đội vừa tăng từ -3k lên +3k khác với đội từng +8k rồi rơi về +3k. Không được dùng future rolling window (chỉ rolling **backward**).

**Nhóm XP và bất đồng**: gold tăng nhưng XP không tăng có thể cho thấy lợi thế chưa chuyển hóa thành sức mạnh level. `gold_xp_gap`, growth, volatility, gradient, reversals. Không tự kết luận XP gây ra thắng; chỉ kiểm tra dự báo.

**Nhóm player role**: một đội +5k vì một carry giữ gần hết tài nguyên có thể khác đội +5k phân bổ đều. Top1, top2, bottom2, median, Gini concentration, last hits, denies, growth của role. `p_gold_top2_share_diff` là khác biệt share tài nguyên top2 giữa hai đội. **Gini** đo bất bình đẳng phân bổ, không phải “đội mạnh hơn”.

**Nhóm objective**: kill, tower, rax, Roshan, Aegis, high-ground, tempo, recency. Phá tower có thể chuyển hóa vàng thành kiểm soát bản đồ. Rủi ro dữ liệu: event Roshan kill chưa có owner side; không được gán phe qua đoán mò từ Aegis.

**Nhóm item**: item hoàn thành, Blink Dagger/BKB và thời điểm mua, trạng thái buyback. Item completion có thể thay đổi mạnh khả năng giao tranh. **P20** là ý tưởng tốt nhất về development point estimate, nhưng chưa qua gate.

**Nhóm tương tác**: `gold_tower_mismatch`: hơn vàng nhưng bị mất nhiều công trình; `gold_vol_adj`: cân nhắc độ nhiễu cùng lúc với lợi thế. Các feature này diễn đạt ý tưởng hay nhưng phải qua grouped forward validation.

## 5. Bảng 28 ý tưởng P01-P28: hiểu câu hỏi, không học thuộc code

Mỗi một dòng là **đã thử** trong lịch sử development, không phải một chứng minh khoa học rằng feature có giá trị. Điểm và CI gốc nằm đầy đủ ở `docs/CREATIVE_FEATURE_EXPERIMENT_ATLAS.md`.

| ID | Câu hỏi sinh ra feature |
| --- | --- |
| P01 | Quan hệ gold với win probability có **lồi** (convex) hay không? |
| P02 | Quan hệ slope gold–win ở đầu/cuối game có liên tục không? |
| P03 | Biến đổi gold `asinh` có giữ thông tin khi gold rất lớn không? |
| P04 | Độ cong thời gian được mô hình hóa mượt có bền không? |
| P05 | Gold tương đối thay vì gold thô có ích không? |
| P06 | XP có đại diện cho sức mạnh thực tế của gold không? |
| P07 | Tập trung vàng vào top-two carry có tác động dự báo không? |
| P08 | Topology support/farming giúp nhìn ra sự khác biệt bị gold lead che khuất không? |
| P09 | Một cú thay đổi gold trong 5 phút có dự báo được reversal không? |
| P10 | Gold lead đang tăng **nhanh dần** hay giảm tốc? |
| P11 | Volatility ngắn hạn có biểu thị trận bất ổn không? |
| P12 | Lợi thế duy trì cùng một hướng trong bao lâu? |
| P13 | Trọng số cho từng công trình có làm tốt hơn count thô không? |
| P14 | Tower bị phá gần đây có giúp dự báo bước ngoặt không? |
| P15 | Các giao tranh chết người gần đây mang thông tin gì? |
| P16 | Trình tự Roshan rồi tower có ích hơn sự kiện riêng lẻ không? |
| P17 | Aegis vừa nhận có tạo cửa sổ lợi thế không? |
| P18 | Buyback commitment là chi phí quyền chọn chiến thuật nào? |
| P19 | “Hơn vàng nhưng thua công trình” có phải trạng thái mong manh không? |
| P20 | Thời điểm hoàn thành item quan trọng, đặc biệt Blink/BKB, giúp dự báo không? |
| P21 | Xung lực đầu tư item gần đây có bền không? |
| P22 | Mã hóa draft 160 chỉ báo tướng có giúp học matchup không? |
| P23 | Cây phi tuyến nông trên gold/time có tốt hơn logistic không? |
| P24 | Cây macro-state được calibration có tốt không? |
| P25 | Gold và time bằng B-spline cộng tính có ích không? |
| P26 | Kết hợp nhiều structural conversion signals có thắng không? |
| P27 | Gộp event-state signals có tổng quát không? |
| P28 | Time-aware logistic regularization mạnh hơn có ổn định hơn không? |

**Kết quả:** 0/28 đạt gate. P20 có reused VAL LL 0.514098 vs historical M1 0.519346, lợi thế -0.005248. Nhưng P20 chỉ thắng 1/3 earlier TRAIN folds và 28-comparison-adjusted CI [-0.016929,+0.006434] chứa 0. Đây là ví dụ sáng tạo có ích, **không phải một model được chứng minh chiến thắng**.

Riêng P22 có LL 1.581239, tệ bất thường: 160 hero indicators quá nhiều so với số trận độc lập và regularization hiện tại. Kết luận đúng: **cấu hình P22 cụ thể thất bại**, không phải “hero draft vô dụng”.

## 6. Bộ 81 features: phải nhận diện được cách gom nhóm và giới hạn của dữ liệu

81 cột mới chia theo gold 19, XP 13, players 19, objectives 17, interactions 13. Thêm 3 cột M1 thành 84 model inputs. Bảng liệt kê **tên của từng cột** ở Research Atlas, và mã định nghĩa ở `research/rich_feature_engineering.py` nằm trong reviewer branch.

Một phép audit đã thấy:
- `o_roshan_delta` và `o_roshan10_delta` luôn 0. Lý do **không có nguồn phân biệt phe Roshan kill**; 486 event nguồn không có `player_slot/slot`. Không gán bừa owner side từ Aegis.
- `x_economy_gap` trùng `gold_xp_gap`.
- Vậy 78 cột engineered là **distinct, varying** trong cohort này; không phải 78 nguồn độc lập hay có ý nghĩa causal.

Q2 dùng elastic-net 84 cột; Q3 dùng HistGradientBoosting với 84 cột. Trên TRAIN-forward 137 trận/70 groups: Q2−M1 LL +0.017311, Q3−M1 +0.009180; cả hai không qua gate. Vì sao? có thể nhiễu, trùng lặp, correlated minutes, drift hoặc hyperparameters. Không thể suy ra chính xác nguyên nhân chỉ từ hai chênh lệch số.

## 7. Path-dependence Q1: ý tưởng quant quan trọng nhất

Hai trận đều hiện +3k gold nhưng lịch sử đến vị trí đó có thể khác:
- **Giả định A:** -2k → +0k → +3k: vừa lật thế.
- **Giả định B:** +8k → +5k → +3k: đang đánh mất lợi thế.

Q1 kiểm tra xem **đường đi trong quá khứ** có giúp dự báo thêm thông tin ngoài gold hiện tại + minute không. Có 5 input: `gold_k`, `minute10`, `adverse_excursion10_k`, `signed_realized_vol10_k`, `directional_efficiency10`.

- Adverse excursion: mức thoái lui từ cực trị gần đây theo chiều phe đang dẫn.
- Signed realized volatility: độ lớn biến động từ các thay đổi gold từng phút, gắn dấu theo trạng thái hiện tại.
- Directional efficiency: `(gold_now-gold_10min_ago) / (sum(abs(one-minute changes)) + epsilon)`, gần +1 nghĩa hầu hết chuyển động có cùng một chiều, gần 0 nghĩa đi qua lại nhiều.

Q1 kiểm tra prefix-only và symmetry khi đổi Radiant/Dire. TRAIN-only forward Q1 LL 0.605963 vs M1 0.612086; Q1−M1 CI 95% [-0.017362,+0.004680] vẫn cắt zero. Q1 tốt hơn 3/4 folds; **không được tuyên bố Q1 đã thắng đáng tin cậy và không thay notebook TEST**.

## 8. Tại sao thử XGBoost, LightGBM nhưng không dùng?

XGBoost và LightGBM xây nhiều cây quyết định nhỏ theo boosting để học mối liên hệ phi tuyến. Với 84 input và chỉ vài trăm trận độc lập, có nguy cơ học lệch một vài patch/series. Không cần model phức tạp nếu không thắng proper score.

Trên **cùng 137 TRAIN-forward games**, LL: Q1 0.605963, M1 0.612086, XGB3 0.615597, LGB3 0.616196, XGB84 0.621809, LGB84 0.622936. Mọi boosted candidate thua Q1 về log loss điểm. Nested tuning thử conservative/moderate/flexible (2 inner chronological group folds bên trong mỗi outer fold) và 16/16 lựa chọn vẫn là conservative. Điều này **không chứng minh** rằng mọi cấu hình XGB/LGBM sẽ thất bại; chỉ là các cấu hình đã chạy không biện minh việc đổi.

Mô hình được chọn bằng nhiều lần xem nhãn cũ dễ mắc **multiple testing / winner's curse**: sau 100 thử nghiệm, có thể tìm thấy một kết quả đẹp do may mắn. Bởi vậy không tiếp tục đào bới hàng trăm tổ hợp trên cùng dataset để đạt điểm số vẻ ngoài.

## 9. Metrics: tự tính loss và hiểu vì sao có CI

Với nhãn `y in {0,1}`, dự báo `p`:
- `log_loss = -y*ln(p)-(1-y)*ln(1-p)` (càng thấp càng tốt).
- `brier = (p-y)^2` (càng thấp càng tốt).
- **Calibration**: khi forecast 70% trên nhiều trường hợp, observed win rate cần gần 70%; ECE10 gom vào mười bins có trọng số.

**Ví dụ giả định**: dự báo 0.9 và Radiant thắng (y=1): log loss 0.105, Brier 0.01; nếu Radiant thua (y=0): log loss 2.303 và Brier 0.81. Tự tin nhưng sai bị phạt mạnh.

**Kết quả TEST thật 106 games, 3.836 minute rows:** M0 LL 0.516444/Brier 0.171912; M1 LL 0.504015/Brier 0.168353. Hiệu số point LL M1−M0 = -0.012430. Nhưng match-level paired 95% CI [-0.0304,+0.0014] chứa 0; 30+ Brier M0 0.1028, M1 0.1074 tệ hơn. **Không nói đã chứng minh M1 hơn; shadow only.**

Vì minute rows cùng match lệ thuộc, bootstrap phải lấy mẫu **cả match hoặc cả professional series**. Với n=3.836 phút nhưng chỉ 106 trận, bootstrap 3.836 hàng độc lập có thể làm khoảng tin cậy quá hẹp.

Với 28 ứng viên thử cùng reused VAL, cần điều chỉnh nhiều phép so sánh như max-T hoặc Bonferroni. Kể cả khi sửa cho 28 phép thử, các **nhiều vòng search trước đó** vẫn tạo selection bias; không xem như confirmatory.

**Equal-game vs per-minute estimand:** per-minute LL cho trận dài nhiều trọng số; equal-match LL cho mỗi trận 1 trọng số. `MATCH_EQUAL` là cách huấn luyện theo trận, nhưng các tập March/October/November không cho cùng một người thắng. Không được chọn lại metric sau khi thấy điểm.

## 10. Leakage và ba loại “đến đúng lúc”

**Leakage từ tương lai trong feature:** forecast phút t chỉ dùng gold history qua phút t, kill/objective event có timestamp <=60t. `prefix_truncated` xóa tương lai rồi tính lại; tất cả 18.292 original snapshots qua test, từ cache gốc. Nhưng đôi khi nguồn lịch sử xuất data ở cuối trận và parser tái tạo bảng; event timestamp nội bộ chưa chứng minh arrival time thực tế.

**Label maturity:** trận đã bắt đầu không đồng nghĩa kết quả đã biết. Có 5 trận TRAIN chưa kết thúc khi VAL bắt đầu; refit trên 286 completed games vẫn chọn M1 trên **VAL cũ**. Đây là sensitivity chứ không phục hồi blind TEST.

**Terminal boundary:** dữ liệu ở đúng giây trận kết thúc không còn là cơ hội forecast trước kết quả. Sau khi TEST đã được xem, loại 12 terminal rows (8 TRAIN,3 VAL,1 TEST); kết quả sửa tốt hơn về correctness nhưng TEST **không còn blind hoàn toàn**.

**Received-at:** một kill có event timestamp 10:00 nhưng API chỉ đưa vào 10:05. Để nói mô hình live, cần log `event_time`, `received_at`, feed completeness/watermark, model version và missing/no-data policy. Simulated lags không thay thế thu thập stream thật.

**Stale-feed bug học được:** với delay d=3 phút mà t=0,1,2, trước đây một thí nghiệm đã dùng `gold[0]` dù nó chưa tới. Sau sửa: `NO_DATA` → p=0.5, không gọi model; từ t>=d mới dùng lịch sử hợp lệ. Đây là sửa correctness trong **research simulation**, không phải code production đã deploy.

## 11. Đọc 16 code cells theo nhóm

1. **Cell 1-3:** setup versions, freeze 500 OpenDota match IDs, refetch, manifest 250/250 patch, provenance.
2. **Cell 4:** time-safe `snapshot_features(match,t)`, gold/XP histories, objective events.
3. **Cell 5:** prefix-deletion check chống future data.
4. **Cell 6:** chronological and series-disjoint split 291/103/106, mature-label sensitivity.
5. **Cell 7:** four models M0-M3, imputer/scaler/logistic fit TRAIN, select M1 using VAL.
6. **Cell 8:** TEST `predict_proba`, log loss/Brier, paired full-match bootstrap.
7. **Cell 9-13:** charts, calibration, equal-match metrics, terminal sensitivity, gold/time mechanics and observed leader-state examples.
8. **Cell 14:** export 3.836 TEST predictions, figure hashes, provenance.
9. **Cell 15-16:** appended **after TEST inspection**; point-in-time/saved scores/label-maturity QA; *không* biến TEST đã dùng thành blind.

Bạn phải chỉ được trong notebook đường gọi `fit` và `predict_proba`. Mở từng cell, đọc một mẫu dữ liệu đầu vào và tự giải thích tại sao một cột hợp lệ ngay ở phút t.

## 12. Nếu là Senior Data Scientist Vexil, mình sẽ hỏi gì?

**Q1: Why logistic baseline?** Đề yêu cầu; dễ đọc, ít tham số, hỗ trợ xác suất và phù hợp số trận độc lập nhỏ.

**Q2: What was creative?** Nhóm cơ chế: time interaction, gold momentum/drawdown/volatility, XP divergence, player allocation Gini, tower/Roshan/Aegis, buyback, Blink/BKB timing, draft, path risk, 81-feature signals, boosting; nhiều ý tưởng không được giữ vì thiếu out-of-sample evidence.

**Q3: Why didn't your best P20 win?** LL historical reused-VAL thấp nhất nhưng adjusted interval qua 28 comparisons chứa zero và chỉ tốt hơn ở 1/3 forward TRAIN folds. Nó đã được search trên reused VAL, không phải fresh validation.

**Q4: Why not just XGBoost with more features?** Strong baselines first. XGB84 0.621809 vs Q1 0.605963 on fixed TRAIN-forward sample; nested tuning không cứu. Tăng feature còn rủi ro trùng và thiếu dữ liệu Roshan owner.

**Q5: What exactly is Q1's novelty?** Không phải phát minh state-of-the-art. Đó là một hypothesis về path-dependent drawdown/volatility/efficiency trên gold history, được kiểm tra theo prefix, group-forward và rejected by a strong M1 comparison interval.

**Q6: Why not promote M1?** TEST point estimates tốt, grouped CI chứa 0, 30+ Brier xấu hơn, một match 55 phút đóng góp 54.9% LL gain, nên shadow-only.

**Q7: Did you solve live forecasting?** Không. Historical OpenDota event timestamps không thay bằng receive timestamps. Pipeline có time-safe historical features; cần source watermark, completeness và actual live data collector trước khi production.

**Q8: Did you do all coding manually?** Không nói sai. AI assistance đã khai báo trong report. Trình bày chính xác những việc bản thân thực sự định hướng, kiểm tra, quyết định và hiểu; không tự nhận mình viết độc lập mọi dòng hoặc tự bịa số giờ làm.

**Q9: What's the one next experiment?** Chốt candidate + decision gate **trước khi thấy kết quả**, thu một cohort mới đủ independent professional series/league với `received_at`, primary minute LL improvement meaningful (e.g. >=0.005), group-CI excludes zero, late30 Brier non-regression, then decide again.

## 13. Bài tập tự kiểm tra

1. Tính p sigmoid với z=0 và z=2, giải thích ý nghĩa.
2. Vì sao 500 trận/18.292 minute rows không phải 18.292 independent games?
3. Tại phút 20, gold tới phút 21 có hợp lệ không? Một event xảy ra phút 19 nhưng được nhận phút 22 có hợp lệ không?
4. Tính log loss khi p=0.99 và y=0; so với p=0.55,y=0.
5. M1 LL nhỏ hơn M0 nhưng CI [-0.0304,+0.0014] chứa zero: được nói gì?
6. P20 đã cải thiện historical VAL, vì sao vẫn phải reject?
7. Nêu 5 feature families, số field từng family và lỗi 2 Roshan + 1 duplicate.
8. Q1 khác M1 ở đâu? Kể tên đầy đủ 5 inputs.
9. Vì sao bỏ một match khiến mức LL gain giảm mạnh là rủi ro?
10. “Nội bộ có 292 tests PASS” có nghĩa sáng chế feature đã được independent prospective validation không? Vì sao?
11. Đóng vai reviewer: nếu GitHub repo private và bạn gửi một link không cấp quyền, reviewer có đọc được không?
12. Hãy tự kể lại toàn bộ project trong **90 giây bằng lời của bạn**, không nhìn câu mẫu.

**Đáp án định hướng:** (1) 0.5 và 0.881; (2) rows cùng match chia sẻ label; (3) không và không; (4) 4.605 vs 0.799; (5) point estimate favorable, not confirmed; (6) multiplicity/unstable folds/reused labels; (7) 19/13/19/17/13, two constant ownerless Roshan, one duplicate; (8) gold/time plus three prefix-path terms; (9) high influence/no robustness; (10) tests check code contracts, not fresh outcome evidence; (11) không; (12) cần tự trình bày.

## 14. Thứ tự học hợp lý

Đọc `REPORT.pdf` 4 trang → mở notebook xem 16 code cells → đọc `docs/CREATIVE_FEATURE_EXPERIMENT_ATLAS.md` → mỗi ngày tự giải thích 5 giả thuyết P01–P28 → đọc các readout Q1/81/boosting → tự tính metrics → luyện trả lời Q1–Q9 tiếng Anh.

Không học thuộc một bài nói AI viết thay rồi tự nhận nghiên cứu mình hiểu. Cần tự chạy/đọc được các đoạn code và tự giải thích quyết định **giữ M0, M1 shadow-only** với đúng giới hạn dữ liệu.
