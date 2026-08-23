# P13 — Fresh BEV Baseline & Cell/Pack → Vehicle Incremental Energy Translation

### 1. Governing Files Read

`PROJECT_INSTRUCTIONS.md`, `docs/IMPLEMENTATION_SPEC.md`, `docs/P12_NMC_DEGRADATION_VALIDATION_REPORT.md`, `docs/CANONICAL_DATA_DICTIONARY.md`, `docs/P11R_BLOCKER_RESOLUTION_REPORT.md`, `docs/RESEARCH_DECISION_LOG.md`, `results/intermediate/p12_degradation_model_parameters.json`, altı zorunlu P12/TUM Parquet dosyası ve `data/processed/tum_id3_pack_architecture.yaml` tamamen incelendi. P12'nin kaynak rolleri, 25°C/%50 SOC referansı, 10-ms birincil ve ayrı 1-s alternatif tanımları ile sıfır ekstrapolasyon kuralı değişmeden uygulandı.

### 2. Frozen P12 Inputs

- Birincil: Luh NMC, 25°C, %50 SOC, aynı-hücre/aynı-SOC bazlı `R10/R10_0`, bounded-monotone central representation.
- Alternatif: bağımsız `R1s/R1s_0` representation; 10-ms ile birleştirilmedi.
- Fiziksel kapasite: yalnız `reconstructed_capacity_retention = measured_capacity_ah / same-cell baseline capacity`; `source_capacity_soh_percent` provenance alanı olarak kaldı ve hiçbir usable-energy/range hesabına girmedi.
- Schreiber: yalnız independent automotive envelope; primary fit'e girmedi.
- TUM ID.3: yalnız fresh HPPC/WLTP plausibility; U.S. arketipi veya yaşlanma eğrisi olmadı.
- Ortak geçerli merkez düğüm alanı: direnç için 0–436.9068 gün; P12 doğrulanmış üst sınırı 447.8987 gündür. Kapasite gözlemleri 448.1849 güne kadar mevcuttur. Alan dışı istek üretilmedi.

### 3. Representative BEV Archetype Assessment

Seçim kriterleri sonuçlardan önce kilitlendi: U.S. light-duty, midsize passenger class, resmî NREL/Argonne satırı, yeniden çalıştırılabilir FASTSim modeli, ticari marka ana model olmayacak, UDDS ve HWFET ayrı tutulacak ve degradation penalty seçim ölçütü olmayacaktı.

Resmî 2024 Transportation ATB arşivinde dört Midsize BEV range üyesi bulundu. 2023 `Mid` trajectory'nin 300-mile satırı güncel model yılı, business-as-usual teknoloji trajectory'si ve orta-uzun menzil sınıfı olduğu için seçildi. ATB'nin kaynak alanı `ANL, Autonomie (2023)` olup dayanak çalışma Argonne'un [ANL/TAPS-23/3 raporudur](https://publications.anl.gov/anlpubs/2023/11/186057.pdf). ATB tanımlarına göre light-duty fuel economy 55% UDDS/45% HWFET ve adjusted real-world temellidir; BEV değerleri charging/EVSE losses içerir ([NREL ATB definitions](https://atb.nlr.gov/transportation/2024/definitions), [BEV assumptions](https://atb.nlr.gov/transportation/2024/battery_electric_vehicle_assumptions)).

### 4. Locked Representative Archetype

Kilitli ana model `P13_US_LDV_MIDSIZE_BEV_2023` adlı markasız U.S. light-duty midsize BEV arketipidir.

| Attribute | Locked value | Role/source |
|---|---:|---|
| Vehicle class | U.S. Light Duty / Midsize / BEV | NREL Transportation ATB 2024 |
| Range member | 300 mile | ATB classification; mobility threshold değildir |
| Nominal pack energy | 77.413145 kWh | ATB 2023 Mid row |
| ATB external energy | 270.072194 Wh/mi = 167.815 Wh/km | charging-inclusive external benchmark only |
| Usable energy | source value missing | uydurulmadı; 0.85/0.90/0.95 usable-window scenarios |
| Mass | 1689.0645 kg | FASTSim 3.0.6'daki iki U.S. BEV definition midpoint |
| Cd / frontal area | 0.2695 / 2.308449 m² | aynı pre-specified midpoint rule |
| Rolling coefficient | 0.007383603 | aynı pre-specified midpoint rule |
| Motor / pack max power | 194.070 / 183.114 kW | aynı pre-specified midpoint rule |
| Nominal voltage scenarios | 350.4 / 394.2 / 438.0 V | 96s / 108s / 120s topology bounds |

`2020 Chevrolet Bolt EV thrml.yaml` yalnız FASTSim 3.0.6 veri-yapısı ve component-map şablonudur; isim, sınıf, pack size ve vehicle-level parametreler kilitli markasız arketiple değiştirilmiştir. Hiçbir ticari araç universal ana model olarak sunulmamıştır. Bu sentezlenmiş vehicle-parameter rule generalizability belirsizliği P13 sonucunun bounded olmasının bir nedenidir.

### 5. FASTSim Configuration and Version

Kurulu sürüm simulation öncesi ve testte tam olarak `3.0.6` doğrulandı; paket yükseltilmedi. Resmî [FASTSim repository](https://github.com/NatLabRockies/fastsim) içindeki `udds.csv` ve `hwfet.csv` cycles kullanıldı. FASTSim yalnız fresh vehicle physics, cycle demand, terminal power, SOC ve storage loss üretti; capacity/resistance ageing üretmedi.

### 6. Fresh Vehicle Baseline

| Cycle | Distance (km) | Stored-energy draw (kWh) | L2 battery-side (kWh/km) | Terminal net (kWh/km) | Fresh storage loss (kWh) | Terminal power range (kW) |
|---|---:|---:|---:|---:|---:|---:|
| UDDS | 11.9904 | 1.031707 | 0.086044 | 0.085326 | 0.008613 | −25.085 to 37.746 |
| HWFET | 16.5068 | 1.684300 | 0.102037 | 0.101555 | 0.007954 | −35.614 to 31.163 |
| 55/45 combined | — | — | 0.093241 | 0.092629 | 0.000612 kWh/km | −35.614 to 37.746 |

Her iki trace de eksiksiz karşılandı. UDDS SOC 1.0000→0.98667, HWFET 1.0000→0.97824 oldu. Negatif terminal power regenerative charge yönünü, pozitif power discharge yönünü korur.

### 7. Energy-Boundary Verification

- `L1`: sabit mechanical/traction mobility service — drive-cycle speed/distance trace.
- `L2`: HV battery-side electrical/stored-energy requirement — P13 primary boundary. Terminal electrical energy ve internal storage loss ayrıca kayıtlıdır.
- `L3`: grid-side electricity — hesaplanmadı.

FASTSim stored-energy draw, terminal net energy ve internal storage loss ayrı alanlardır. Sevdari conversion uygulanmadı; ATB charging-inclusive benchmark'a ikinci charging loss eklenmedi.

### 8. Capacity-State Scaling

`state_kind=capacity` Luh gözlemlerindeki `reconstructed_capacity_retention` direnç exposure düğümlerinin sabit ara-bölmelerinde özetlendi. Her düğümde median/q10/q90 hesaplandı ve fiziksel non-increasing bound uygulandı; gün 0 tam olarak 1.0'dır. Central fiziksel retention doğrulanmış düğümlerde 1.0000→0.82539 aralığındadır.

Capacity yalnız nominal pack energy × usable-window × retention ile usable stored energy ve technical range precursor'u etkiler. Traction kWh/km capacity loss ile bölünmedi veya doğrudan ölçeklenmedi. ATB usable-energy alanı boş olduğu için taze usable window 0.85/0.90/0.95 senaryoları olarak açıkça korunmuştur. NHTS threshold veya universal 70/80% SOH kullanılmadı.

### 9. Cell-to-Pack Resistance Scaling

Her topology için `I_pack(t) = P_terminal(t) / V_nominal` hesaplandı. Taze effective pack resistance:

`R_pack,fresh = E_storage_loss,fresh / integral(I_pack² dt)`

olarak kalibre edildi. Ardından:

`R_cell-path,aged = R_pack,fresh × cell_share × (R_cell/R_cell,0)`

ve fixed non-cell path `R_pack,fresh × (1 − cell_share)` olarak tutuldu. Eşdeğer hücre direnci yalnız topology identity kontrolü için `R_cell = R_cell-path,pack × Np/Ns` ile raporlandı; absolute Luh cylindrical-cell Ω hiçbir zaman arketip pack Ω'ına eşitlenmedi.

96s/108s/120s senaryolarında effective fresh pack resistance 0.03585–0.05839 Ω oldu. Topology mapping deterministic'tir; aynı relative cell-ageing signal farklı voltage/current architecture'lerinde fiziksel olarak aynı enerji identity'sini korur.

### 10. Fresh-Pack Loss Decomposition

FASTSim fresh storage loss, cell-sensitive ve fixed non-cell yollarına ayrıldı. `cell_resistance_share_of_ageing_sensitive_pack_loss` sonuçlardan önce 0.50/0.75/1.00 sensitivity scenarios olarak kilitlendi. 1.00 all-cell conservative upper bound'dur; 0.50 ve 0.75 non-cell busbar/contact/BMS/current-path paylarını açıkça koruyan engineering brackets'tir. Bunlar probability veya fitted central estimate değildir.

Bu share doğrudan bir representative U.S. pack teardown ölçümüyle tanımlanmadığı için tüm sonuçlarda korunur ve tek değere indirgenmez. Bu sınırlılık hard blocker değil, `WITH BOUNDS` nedenidir.

### 11. Candidate Translation Representations

1. `T1 — Physics-based resistance-loss increment`: bidirectional cycle power→current, effective resistance ve `I²Rdt`. Tam veri gereksinimi karşılandı.
2. `T2 — Equivalent power-loss formulation`: `P/V→I` ile T1'in cebirsel eşdeğeri; bağımsız ikinci sonuç olarak çalıştırılmadı çünkü yeni kanıt sağlamaz.
3. `T3 — Bounded effective-loss representation`: bilinmeyen cell/non-cell decomposition'u 0.50/0.75/1.00 share scenarios ile sarar; T1'in uncertainty wrapper'ıdır.

Empirical SOH→kWh/km shortcut değerlendirmeye alınmadı.

### 12. Selected Primary Translation

Primary translation `T1_PHYSICS_BASED_RESISTANCE_LOSS_INCREMENT` seçildi ve config'de outcome sonuçları görülmeden önce kilitlendi:

`ΔE_loss = integral[I_pack(t)² × R_cell-path,fresh × (R_rel − 1) dt]`.

Kodda aynı identity `fresh_storage_loss × cell_share × (R_rel − 1)` biçiminde uygulanır. Bu, cell resistance artışını tüm vehicle energy'ye değil yalnız ilgili taze resistive-loss component'ine uygular. Fixed non-cell loss yaşlanmaz.

### 13. 10-ms Primary Energy Penalty

Luh central 10-ms states için `R/R0` 1.0000→1.12377'dir. Pre-specified topology, cell-share ve usable-window scenarios boyunca incremental energy:

- taze noktada: 0;
- en yüksek doğrulanmış central state'te: en fazla 0.00008890 kWh/km;
- vehicle battery-side energy artışı: en fazla 0.10332%.

0.90 usable-window ve 108s örneğinde UDDS technical range precursor 809.7→667.8 km oldu; bunun baskın nedeni usable-capacity azalmasıdır, resistance energy penalty değil. Bu bir mobility adequacy kararı değildir.

### 14. 1-s Alternative Energy Penalty

Luh central 1-s states ayrı tutuldu; `R/R0` 1.0000→1.24738. Aynı bounded pack assumptions altında:

- incremental battery-side energy: en fazla 0.00017769 kWh/km;
- vehicle battery-side energy artışı: en fazla 0.20651%.

1-s değerler 10-ms curve'e karıştırılmadı ve primary olarak yükseltilmedi.

### 15. Physical Uncertainty Architecture

Belirsizlik katmanları ayrı alanlarla korunur: P12 10-ms central/empirical bounds, ayrı P12 1-s central/empirical bounds, reconstructed capacity median/q10/q90, 96s/108s/120s voltage/topology, 0.50/0.75/1.00 cell-sensitive loss share ve 0.85/0.90/0.95 fresh usable window.

`AUTOMOTIVE-COMPATIBLE ENVELOPE` içindeki early Schreiber states en fazla 0.05690% penalty verdi. `EXTREME / CONDITIONAL ENVELOPE` — Luh tails, commuter contact-sensitive ve highway post-knee dahil — 2.57093 resistance ratio ve en fazla 1.31144% penalty'ye ulaştı. Bu tail primary trajectory değildir.

### 16. TUM HPPC/WLTP Validation Method

TUM cell HPPC 10-ms ve 1-s resistance değerleri yalnız resmî 108s2p architecture ile `R_pack = R_cell × 108/2` ölçeğine taşındı. 0/20/40°C ayrı kaldı. WLTP'nin 322,720 adet 100-ms sample'ında measured voltage × current zamanla integre edildi; speed aynı timestamps ile distance'a çevrildi. Main U.S. arketip parametresi TUM'a fit edilmedi.

### 17. TUM Validation Results

- Measured WLTP voltage/current: 354.75–452.50 V ve −168.87–168.36 A.
- TUM WLTP net battery energy: 133.525 Wh/km.
- TUM 20°C pack HPPC: 10-ms 0.06795–0.07265 Ω; 1-s 0.08495–0.09916 Ω.
- P13 fresh effective pack resistance: 0.03585–0.05839 Ω.
- Temperature response fiziksel: median resistance 0°C→20°C→40°C monotonik azaldı.

P13 voltage/current ve resistance scale aynı automotive büyüklük mertebesindedir. FASTSim combined 93.241 Wh/km, TUM WLTP'nin 0.698 katıdır; araç/cycle/boundary farkları dikkate alındığında order-of-magnitude compatible, exact calibration değildir. TUM validation classification: `PASS WITH BOUNDS`.

### 18. External Energy Plausibility

ATB dış kıyası 167.815 Wh/km'dir ve charging-inclusive, adjusted real-world boundary'dedir. P13 FASTSim combined L2 değeri 93.241 Wh/km olup ATB'nin 0.556 katıdır. Doğrudan equality beklenmez: P13 unadjusted two-cycle fresh battery-side, ATB ise 55/45 adjusted real-world ve charging-inclusive'dır. Değerler aynı büyüklük mertebesindedir; charging conversion uygulanmadan boundary farkı açık bırakıldı. Classification: `PASS WITH BOUNDS`.

### 19. Valid Translation Domain

Primary/alternative Luh results yalnız P12 observed exposure nodes 0–436.9068 gün içinde üretildi. P12 resistance limit 447.8987 gün, capacity limit 448.1849 gündür. Schreiber satırlarında exposure pooling yapılmadı; status `INDEPENDENT_AUTOMOTIVE_VALIDATION_STATE` olarak kaldı. Alan dışı API/translation isteği için kilitli cevap `OUTSIDE_VALIDATED_DEGRADATION_DOMAIN`'dir.

### 20. False-Optimum Energy Gate

Gelecek lifecycle modelinde bir translation aşağıdakilerden herhangi birine dayanırsa `REJECTED / NON-ROBUST` sayılacaktır: direct `%R = %kWh/km`; all-pack resistance'ın otomatik yaşlanması; unsupported tek fresh resistance; unsupported tek topology; yalnız P12 extreme tail; automotive-incompatible state; extrapolation; TUM-specific forced calibration. P13 carbon veya optimum hesaplamadı.

### 21. Files Created

- `data/raw/SRC_NREL_TRANSPORTATION_ATB_2024/2024_atb_transportation_data_v1.zip`
- `data/metadata/SRC_NREL_TRANSPORTATION_ATB_2024.yaml`
- `src/vehicle_energy/__init__.py`, `p13_config.yaml`, `p13_pipeline.py`
- Beş P13 processed Parquet ve altı processed metadata YAML dosyası
- `results/intermediate/p13_vehicle_energy_model_parameters.json`
- `results/intermediate/p13_artifact_manifest.json`
- İki internal diagnostic PNG
- `tests/test_p13_vehicle_energy.py`
- `docs/P13_VEHICLE_ENERGY_TRANSLATION_REPORT.md`

### 22. Files Modified

- `data/metadata/SOURCE_MANIFEST.csv`: resmî NREL Transportation ATB 2024 source inventory'ye eklendi.
- `tests/test_raw_data_provenance.py`: beklenen kaynak sayısı 14→15 olarak güncellendi; test mantığı değişmedi.
- `docs/RESEARCH_DECISION_LOG.md`: yalnız final gate sonrasında P13 kaydı eklenecektir.

P11/P12 scientific outputs overwrite edilmedi.

### 23. Tests Run

- P13 scientific tests: `13 passed`.
- Tam repository suite: `41 passed`.
- İki ardışık final generation: manifestli `21/21` artifact SHA-256 değerleri aynıdır.
- FASTSim exact-version, no-ageing role, boundary separation, physical capacity field, no direct R shortcut, fixed non-cell paths, topology identity, source-role guards, no extrapolation, no carbon/lifecycle imports, bidirectional power ve TUM temperature ordering test edildi.

### 24. Scientific Simulation Performed

Fresh/reference simulations: markasız representative U.S. midsize BEV için FASTSim 3.0.6 üzerinde bir UDDS ve bir HWFET fresh drive-cycle simulation.

Degradation-state energy simulations: FASTSim yeniden yaşlandırılmadı. Frozen fresh power/loss trace üzerinde 16 Luh 10-ms central, 16 Luh 1-s central, bunların P12 empirical-tail states'i ve observed Schreiber validation states; iki cycles × üç topology × üç cell-loss share × üç usable-window scenarios ile deterministic T1 translation uygulandı. Toplam 4,428 energy rows üretildi.

### 25. Carbon Calculation Performed

NONE

### 26. Extrapolation Performed

NONE

### 27. Frozen-Decision Changes

NONE

### 28. Remaining Validation Items

Gelecekte, P13 gate'i yeniden açmadan veya central sonucu değiştirmeden önce şu bounded items bağımsız veriyle daraltılabilir: representative U.S. midsize pack için measured cell/non-cell loss decomposition; markasız arketipin daha geniş resmî vehicle-parameter ensemble'ı; battery-side ile adjusted wall-side arasındaki controlled charging/test-procedure bridge; NHTS technical mobility threshold (bilerek sonraya bırakıldı).

### 29. Hard Blockers

NONE. Physical capacity scaling reproducible'dır; FASTSim battery-side physics yeterlidir; topology-aware relative signal transfer absolute cross-cell equality gerektirmez; TUM çelişki göstermemiştir. Kalan pack decomposition ve archetype generalizability unsurları explicit bounded uncertainty olarak taşınmıştır.

### 30. Final Status

VEHICLE ENERGY TRANSLATION VALIDATED WITH BOUNDS
