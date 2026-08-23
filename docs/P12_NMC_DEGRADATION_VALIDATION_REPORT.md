# P12 — NMC Degradation-State Construction & Automotive Validation

### 1. Governing Files Read

Aşağıdaki dondurulmuş yönetişim ve lineage dosyaları tamamen okundu: `PROJECT_INSTRUCTIONS.md`, `docs/IMPLEMENTATION_SPEC.md`, `docs/CANONICAL_DATA_DICTIONARY.md`, `docs/P11_PREPROCESSING_REPORT.md`, `docs/P11R_BLOCKER_RESOLUTION_REPORT.md`, `docs/RESEARCH_DECISION_LOG.md` ve Luh, Schreiber, TUM seçim kayıtları. P11/P11R canonical Parquet şemaları, metadata ve kaynak arşiv yapıları da denetlendi.

Bilimsel roller değiştirilmedi: Luh & Blank primary fitting kaynağı; Schreiber bağımsız automotive validation kaynağı; TUM ID.3 yalnız taze HPPC/electrical plausibility kaynağıdır. Kaynak bağlamı [Luh & Blank 2024](https://doi.org/10.1038/s41597-024-03831-x), [Schreiber et al. 2025](https://doi.org/10.1016/j.est.2025.115357), [resmî güncellenmiş Schreiber veri seti](https://mediatum.ub.tum.de/1755598) ve [TUM ID.3 veri seti](https://mediatum.ub.tum.de/1656314) ile doğrulandı.

### 2. Baseline Definition Assessment

| Candidate | Değerlendirme | Gerekçe |
|---|---|---|
| A — aynı hücre ve SOC için ilk geçerli RT pulse check-up | Seçildi | `is_rt`, `soc_nom`, ölçülen sıcaklık, timestamp ve iki ayrı direnç timescale'i doğrudan kaynakta mevcut. |
| B — source-identified fresh check-up | Ayrı kural olarak seçilmedi | PLSV2 içinde bağımsız bir `fresh` etiketi yok; ilk geçerli kronolojik RT check-up aynı savunulabilir başlangıcı, ek etiket varsaymadan verir. |
| C — source-supplied initial resistance alanı | Kullanılamaz | Seçilen 10-ms ve 1-s ölçümleri için ayrı bir başlangıç direnci alanı yok. |

Kural, herhangi bir R/R0 hesabı veya degradation outcome incelemesinden önce `src/degradation/p12_config.yaml` içinde `BASELINE RULE LOCK` olarak kaydedildi. Carbon, replacement, lifecycle veya retirement sonucu baseline seçimine girmedi.

### 3. Locked Baseline Rule

Kilitli kural `luh_same_cell_soc_rt_first_valid_v1`'dir: `(cell_key, soc_nom)` içinde `is_rt == 1`, 25 ± 0,5°C, SOC ∈ {10, 30, 50, 70, 90}, iki direnç için kaynak-dokümante 1–1000 mΩ aralığı ve finite alanlar sağlandıktan sonra `(timestamp_s, sd_block_id)` sıralamasındaki ilk durum baseline'dır.

228 hücre × 5 SOC = 1.140 baseline'ın tamamı bulundu; eksik baseline yoktur. Başka hücre, başka SOC, başka sıcaklık temeli veya başka timescale baseline'ı kullanılamaz. Her waveform bloğu tam 61 satırdır; 2.149.823 waveform satırı 35.243 tekil pulse durumuna tam olarak indirgenmiştir.

### 4. Capacity-State Construction

Primary kapasite durumu kaynak alanı `soh_cap`'tır ve **author-defined percent scale** olarak `source_capacity_soh_percent` adıyla tutulmuştur. Bu değer kapasite fraction değildir; kaynağın EOL-referenced ölçeği nedeniyle ağır yaşlanmış koşullarda sıfırın altına inebilir. Sessizce yeniden hesaplanmamıştır.

Kaynak tanımlı RT check-up discharge ölçümü (`cyc_condition == 2`, `cyc_charged == 0`) ve finite `cap_aged_est_Ah`/`soh_cap` koşulları 3.458 kapasite durumu, 228 hücre ve 76 koşul üretmiştir. Ayrı consistency alanı `reconstructed_capacity_retention = cap_aged_est_Ah / same-cell earliest eligible cap_aged_est_Ah` olarak saklanmıştır. İki ölçek aynı değildir; noktasal median mutlak fark 13,472 percentage point'tir. Bu fark bir overwrite nedeni değil, tanım farkının açık kanıtıdır.

Ageing-type kapsamı: calendar 1.104 gözlem/48 hücre/16 koşul; cyclic 1.695/144/48; profile 659/36/12. Hücre, replicate, condition, sıcaklık, SOC, charge/discharge rate, Ah throughput, operational cycle ve check-up sayıları korunmuştur.

### 5. 10-ms Relative Resistance Construction

Primary durum `R10_rel = R10 / R10_0`'dır. Mutlak `resistance_10ms_ohm`, kaynak mΩ alanı ve `SCIENTIFIC_DERIVED` rolü birlikte korunmuştur. 15.861 geçerli RT pulse durumu üretilmiş; primary reporting SOC olan %50'de 3.164 gözlem, 228 hücre ve 76 koşul kalmıştır. Temel alan missingness'i sıfırdır.

Raporlama SOC'si outcome'dan bağımsız ön-kilitli sıralamayla seçildi: önce hücre kapsamı, sonra koşul kapsamı, sonra missingness, eşitlikte %50'ye yakınlık. Beş SOC'nin tamamı 228 hücre ve 76 koşul kapsadığı için tie-break %50'yi seçmiştir; tüm diğer SOC durumları gözlem artifact'ında korunmuştur.

### 6. 1-s Alternative Resistance Construction

Alternative durum `R1s_rel = R1s / R1s_0`'dır. `resistance_1s_ohm`, baseline ve relative alanları 10-ms alanlarından ayrıdır. 1-s verisi bağımsız veri seti olarak sunulmamış, yalnız alternative physical specification olarak modellenmiştir. 10-ms ve 1-s değerleri hiçbir adımda karıştırılmamış veya ortalanmamıştır.

### 7. Exposure-Axis Assessment

Ortak primary eksen `elapsed_calendar_days_since_same_cell_baseline` olarak seçildi; calendar, cyclic ve profile koşullarının tamamında aynı fiziksel birime sahip tek kaynak-temelli ortak eksendir. Valid domain kapasite için 0–448,185 gün; R10 ve R1s için 0–447,899 gündür.

`charge_throughput_ah`, `discharge_throughput_ah`, `num_cycles_op` ve `num_cycles_checkup` source-native exposure alanları gözlem düzeyinde korunmuştur. Tek bir cycle veya Ah ekseni bütün calendar/cyclic/profile koşullarını eşdeğer biçimde temsil etmediği için primary ortak fit ekseni yapılmamıştır. EFC, kWh, km veya mileage-equivalent exposure türetilmemiştir.

### 8. Candidate Representation Families

En fazla üç ön-kilitli family değerlendirildi: (1) observed/nonparametric 30-günlük cell-balanced median düğümleri, (2) weighted low-order linear trend, (3) bounded monotone isotonic/PAVA. İlk baseline düğümü ayrı tutuldu; model düğümleri yalnız gerçek gözlem zamanları içinde konumlandırıldı.

| Metric | Family | RMSE | Median abs. residual | Monotonicity violations |
|---|---|---:|---:|---:|
| Source capacity SOH (%) | observed | 16,6925 | 9,7209 | 2 |
| Source capacity SOH (%) | linear | 17,4822 | 10,9366 | 0 |
| Source capacity SOH (%) | monotone | 16,6922 | 9,7795 | 0 |
| R10/R10,0 | observed | 0,1640 | 0,0688 | 5 |
| R10/R10,0 | linear | 0,1650 | 0,0709 | 0 |
| R10/R10,0 | monotone | 0,1636 | 0,0687 | 0 |
| R1s/R1s,0 | observed | 0,2036 | 0,0837 | 3 |
| R1s/R1s,0 | linear | 0,2064 | 0,0851 | 0 |
| R1s/R1s,0 | monotone | 0,2037 | 0,0836 | 0 |

Tek R² validity kanıtı olarak kullanılmadı. Residual q10/q90, replicate/condition coverage, valid domain ve extrapolation sayıları machine-readable artifact'ta saklandı.

### 9. Selected Primary Representation

Seçilen central family `bounded_monotone_isotonic`'tir. Seçim nedeni en düşük residual peşinde olmak değil; observed-domain düğümleri, fiziksel yön kısıtı, sıfır extrapolation ve linear forma göre benzer veya daha iyi residual davranışıdır. R/R0 merkezi t=0'da matematiksel olarak tam 1'e ankore edilmiştir; sub-unity ölçülen noktalar gözlem katmanından silinmemiştir.

Bu central summary bir “universal battery curve” değildir. Koşullar pooled bir tek bataryaya dönüştürülmemiş; raw state artifact'ında ve condition/replicate uncertainty katmanlarında tutulmuştur. Model parametreleri ve düğümleri kod içine sonuç sabiti olarak gömülmemiş; Parquet ve `results/intermediate/p12_degradation_model_parameters.json` içinde saklanmıştır.

### 10. Uncertainty Architecture

Olasılık dağılımı varsayılmadı. 240 uncertainty satırı beş açık katman içerir: observed-total empirical q10/q90, condition-içi replicate variability, condition-median variability, üç noktalı within-cell rolling-median measurement proxy ve üç candidate family arasındaki representation range.

“Measurement variability proxy” saf cihaz noise'u olarak yorumlanamaz; gözlem sıklığı ve kısa-ölçekli hücre varyasyonunu birlikte sınırlar. Central, q10 ve q90 birlikte sunulur; tek deterministik eğri yeterli çıktı sayılmamıştır.

### 11. Valid Degradation Domain

Primary kapasite domain'i 0–448,185 gün; primary/alternative direnç domain'i 0–447,899 gün, 25 ± 0,5°C'dir. Primary resistance reporting basis %50 SOC'dir; gözlemsel artifact %10/%30/%50/%70/%90 SOC'yi taşır.

Modelde `extrapolation_count = 0`'dır. Sonraki bir aşama bu domain'i aşmak isterse sonuç üretmek yerine `TECHNICAL / DATA BOUNDARY` uygulanmalıdır. Domain dışı tail, km veya lifetime tahmini yapılmamıştır.

### 12. Schreiber Automotive Validation Method

Schreiber verisi primary fit'e girmedi ve Luh exposure eksenine zorla map edilmedi. Dokuz seçilmiş check-up ayrı doğrulama tablosu oluşturdu.

Kapasite, her dosyada sabit source-protocol `protocol_line == 11` full-discharge segmentindeki Ah span'dan alındı. Direnç, 10% capacity removal ve 1.800-s rest sonrasındaki ilk HPPC discharge pulse'u (`protocol_line == 38`) için tanımlandı: başlangıç örneğine göre `R = |ΔV/ΔI|`; primary t=10 ms, alternative t=1 s; discharge işareti absolute step ile ele alındı. Pulse current step yaklaşık 54–57 A, ölçüm sıcaklığı 20,2–22,0°C'dir. Arbitrary window veya outcome-based pulse seçimi yoktur.

### 13. Schreiber Validation Results

Commuter başlangıç→CU50: capacity retention 1,000→0,9528; R10 1,000→1,4639; R1s 1,000→1,4164. Highway başlangıç→CU11→CU22: capacity retention 1,000→0,9097→0,5073; R10 1,000→1,0682→2,4994; R1s 1,000→1,0673→2,5709. Yönler Luh fiziksel davranışıyla uyumludur ve commuter/highway zarfları belirgin biçimde farklıdır.

Magnitude tam örtüşmez. Schreiber commuter endpoint'ine ±0,025 capacity-retention penceresinde 787 Luh %50-SOC durumu düşer; Luh R10 q10–q90 0,9498–1,0388 ve max 1,2256 iken Schreiber 1,4639'dur. Highway endpoint penceresinde yalnız 7 Luh durumu vardır; Luh q10–q90 1,8135–2,0562 ve max 2,0823 iken Schreiber 2,4994'dür. Ayrıca commuter CU30 direnç sıçraması sonraki CU'da kısmen geri döner; kaynak makale contact-sensitive resistance yorumuna karşı dikkat gerektirir. Bu nedenle validation status `PASS WITH BOUNDS`'dur.

### 14. TUM HPPC Plausibility Role

TUM'un üç taze 0/20/40°C dosyasında sabit `protocol_line == 37` içindeki dokuz tekrarlı discharge pulse segmenti kullanıldı. Her segmentte t=0'dan 10 ms ve 1 s'ye lineer waveform interpolation ile aynı ΔV/ΔI tanımı uygulandı; 27 summary satırı üretildi.

Median taze R10: 0°C'de 1,929 mΩ, 20°C'de 1,294 mΩ, 40°C'de 1,077 mΩ. Median R1s sırasıyla 2,851, 1,611 ve 1,301 mΩ'dur. Bu elektriksel ölçek ve beklenen sıcaklık duyarlılığı extraction yöntemini destekler. TUM hiçbir ageing fit'e, Luh curve'üne veya aged absolute resistance eşitlemesine girmemiştir.

### 15. Automotive Compatibility Envelope

`AUTOMOTIVE COMPATIBILITY ENVELOPE`, ortak bir fit değil, iki kanıt katmanının bounded union'ıdır: Luh'un observed 25°C replicate/condition state-space'i ve Schreiber commuter/highway validation trajectories. TUM yalnız absolute pulse-scale/sıcaklık plausibility kontrolüdür.

Sınıflar:

- `PRIMARY PHYSICAL SPECIFICATION`: Luh %50 SOC, 25°C, 10-ms bounded-monotone central ve empirical bounds.
- `ALTERNATIVE PHYSICAL SPECIFICATION`: ayrı 1-s bounded-monotone representation.
- `AUTOMOTIVE-COMPATIBLE ENVELOPE`: yalnız observed Luh ve observed Schreiber state-space union'ı; exposure pooling yok.
- `EXTREME / CONDITIONAL ENVELOPE`: Luh empirical tails, Schreiber contact-sensitive resistance düzeyleri ve highway post-knee severity.
- `REJECTED AS AUTOMOTIVE-INCOMPATIBLE`: domain-dışı, cross-SOC/cross-temperature baseline, mixed-timescale veya extrapolation gerektiren trajectories.

Pack topology, kWh/km ve carbon bu zarfın parçası değildir.

### 16. Rejected / Conditional Trajectories

Herhangi bir Luh hücresi outcome görünümüne göre elenmedi; 228/228 hücre korunmuştur. Automotive central olarak reddedilenler: observed domain dışı tail'ler, başka hücre/SOC/sıcaklık baseline'ı, 10-ms–1-s karışımı ve Luh/Schreiber arasında uydurulmuş ortak exposure scale'idir.

Conditional kalanlar: Schreiber highway CU22 post-knee noktası, commuter contact-sensitive direnç seviyesi ve Luh q10/q90 uçlarıdır. Bunlar ileri çalışmada central trajectory olarak kullanılamaz; yalnız açık extreme/conditional senaryo olarak değerlendirilebilir.

### 17. Files Created

- `src/degradation/__init__.py`, `src/degradation/p12_config.yaml`, `src/degradation/p12_pipeline.py`
- `data/processed/luh_degradation_state_observations.parquet` — 19.319 satır
- `data/processed/luh_degradation_state_model.parquet` — 144 satır
- `data/processed/luh_degradation_uncertainty.parquet` — 240 satır
- `data/processed/schreiber_automotive_validation_summary.parquet` — 9 satır
- `data/processed/tum_id3_hppc_validation_summary.parquet` — 27 satır
- Yukarıdaki beş dataset için `data/processed/metadata/*.yaml`
- `results/intermediate/p12_degradation_model_parameters.json`
- `results/intermediate/p12_artifact_manifest.json`
- `results/diagnostics/p12_capacity_state.png`, `p12_r10_state.png`, `p12_r1s_state.png`, `p12_automotive_compatibility.png`, `p12_tum_hppc_plausibility.png`
- `tests/test_p12_degradation.py`
- `docs/P12_NMC_DEGRADATION_VALIDATION_REPORT.md`

### 18. Files Modified

- `tests/test_preprocessing.py`: P11 “scientific filtering NONE” invariant'ı yalnız P11 preprocessing metadata'sına scope edildi; P12'nin açıkça bildirdiği bilimsel eligibility kuralları P11 testi tarafından yanlışlıkla yasaklanmıyor.
- `docs/RESEARCH_DECISION_LOG.md`: final gate sonrasında P12 kaydı eklendi.

Hiçbir P11/P11R canonical Parquet dosyası overwrite edilmedi. Raw dosyalar değiştirilmedi.

### 19. Tests Run

Yeni testler baseline determinismi, aynı-hücre/SOC/sıcaklık eşleşmesi, R/R0 matematiği, timescale ayrımı, kaynak rolü koruması, primary domain, artifact manifest ve kapasite alanı ayrımını kapsar.

Nihai tam paket: `28 passed in 45.12s`. İki ardışık nihai tam P12 üretiminde 17 Parquet/JSON/YAML/PNG artifact için SHA-256 karşılaştırması: `17 checked, 0 mismatch`. Beş PNG 1200×750 RGBA olarak açılabildi; kapasite render'ı görsel olarak incelendi, diğer dosyalar boyut/mod/hash ve üretim bütünlüğüyle doğrulandı.

### 20. Scientific Fitting Performed

`capacity_source_soh_percent`, `R10/R10_0` ve ayrı `R1s/R1s_0` için yalnız üç family fit/değerlendirmesi yapıldı: cell-balanced observed median nodes, weighted first-order linear trend ve weighted bounded-monotone PAVA. Primary olarak bounded-monotone representation seçildi. Schreiber ve TUM fitting'e girmedi.

### 21. Scientific Filtering Performed

Capacity: yalnız kaynak-tanımlı RT discharge check-up (`cyc_condition == 2`, `cyc_charged == 0`) ve finite source capacity/SOH. 1.098.399 EOCV satırının 3.458'i bu state grain'ine aittir; protokol koşulundan sonra non-finite kayıt yoktur.

Resistance: 35.243 tekil pulse durumundan 17.698 non-RT durum çıkarıldı; RT işaretli durumlardan 1.684'ü kilitli 25 ± 0,5°C aralığı dışında kaldı. Kalan 15.861 durumda SOC veya 1–1000 mΩ plausibility failure yoktur. Hücre/file outcome, monotonicity veya resistance-growth büyüklüğüne göre hiçbir seçim yapılmadı.

Schreiber/TUM: yalnız önceden sabit source-protocol satırları ve elektriksel ΔV/ΔI tanımı kullanıldı; outcome-oriented filtering `NONE`.

### 22. Extrapolation Performed

`NONE`

Primary ve alternative model düğümlerinin tamamı exact observed domain içindedir; `extrapolation_count = 0`.

### 23. Frozen-Decision Changes

`NONE`

Primary/alternative timescale, kaynak rolleri, 25°C referans, no-outcome-leakage ve P12 scope değiştirilmedi.

### 24. Remaining Validation Items

- Schreiber resistance magnitude'ının central automotive kullanımına alınması için full intermediate CU grid, contact event metadata ve tercihen replicate evidence gerekir.
- Luh source SOH ile capacity-retention aynı metric değildir; iki alanın ayrı tutulması sonraki aşamalarda zorunludur.
- Luh observed domain'i dışındaki ömür/tail davranışı bu aşamada doğrulanmamıştır.
- TUM taze HPPC'dir; ageing trajectory doğrulaması sağlamaz.

Bu maddeler central observed-domain representation'ı engellemez; automotive envelope'ı sınırlar.

### 25. Hard Blockers

`NONE`

Baseline eksiksizdir, iki resistance timescale kurulmuştur, primary fitting yalnız Luh kullanır, automotive validation yön bakımından uyumludur ve bütün test/determinism gate'leri geçmiştir.

### 26. Final Status

`NMC DEGRADATION STATE VALIDATED WITH BOUNDS`

Gerekçe: central Luh capacity/R10 representation observed domain içinde kullanılabilir ve Schreiber automotive evidence ile degradation yönü uyumludur; ancak Schreiber'in matched-capacity resistance magnitude'ları Luh q90/max sınırlarını aşar ve highway post-knee/contact-sensitive bölümler yalnız conditional envelope olarak taşınabilir.

