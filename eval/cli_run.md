# CLI run

**Q (en):** At which stages should wheat be irrigated?
- English query: At which stages should wheat be irrigated?
- Action: `answer` (in domain (best_sim=0.71))
- Answer: • Depending upon the rainfall, irrigate the timely sown crop upto the end of March to avoid the harmful effect of unusual rise in temperature at grain filling/formation stage. [1] The normal practice of applying four to six irrigations (28-42 cm-ha water) are enough for wheat crop. [4]
- [1] Package of Practices for Crops of Punjab - Rabi (doc open12, p. 24) https://pau.edu/content/ccil/pf/pp_rabi.pdf
- [4] Wheat Cultivation in India Pocket Guide (EB-52) (doc icar01, p. 16) https://iiwbr.org.in/wp-content/uploads/2023/08/EB-52-Wheat-Cultivation-in-India-Pocket-Guide.pdf
- Latency: 13.89 s

**Q (en):** What is the seed rate for direct seeded rice?
- English query: What is the seed rate for direct seeded rice?
- Action: `answer` (in domain (best_sim=0.65))
- Answer: Currently, direct seeded rice in Asia occupies about 29 Mha, which is approximately 21 per cent of the total rice area in the region (Pandey and Velasco, 2002). [3] 1 1 10 100 1000 10000 100000 1000000 10 100 1000 25 500 2500 2009 2017 2018 2019 5000 No of happy seeder Area covered (ha) Happy Seeder adoption trend and area covered 15 Direct Seeded Rice (DSR)6 6.1 Background In the IGP , manual transplanting of rice in puddled fields is a common practice in rice- wheat cropping system. [5]
- [3] A Compendium of Key Climate Smart Agriculture Practices in Intensive Cereal Based Systems of South Asia (doc open07, p. 24) https://cgspace.cgiar.org/server/api/core/bitstreams/9977b2a7-99ff-4a4b-b2c7-b7c330a4e7e4/content
- [5] A Compendium of Key Climate Smart Agriculture Practices in Intensive Cereal Based Systems of South Asia (doc open07, p. 22) https://cgspace.cgiar.org/server/api/core/bitstreams/9977b2a7-99ff-4a4b-b2c7-b7c330a4e7e4/content
- Latency: 11.01 s

**Q (en):** How much fertilizer should I apply?
- English query: How much fertilizer should I apply?
- Action: `clarify` (crop-specific advice requested but no crop named)
- Answer: Which crop is this for? If you can, also tell me your district or state and the season (kharif or rabi).
- Latency: 0.07 s

**Q (en):** Who won the cricket world cup in 2011?
- English query: Who won the cricket world cup in 2011?
- Action: `refuse` (out of domain (keywords=False, best_sim=0.42))
- Answer: I can only answer questions about crops, irrigation and fertilizers, based on agricultural advisory documents.
- Latency: 0.08 s

**Q (hi):** सरसों की उपज कैसे बढ़ाएं?
- English query: How to increase the yield of mustard?
- Action: `answer` (in domain (best_sim=0.68))
- Answer: सरसों की फसल के बीज की उपज में माइक्रो-स्पिनकर (सिंचाई दक्षता 60-70%) का उपयोग करके 24% और चेक बेसिन पर ड्रिप सिंचाई (सिंचाई दक्षता 80- 90%) का उपयोग करके 18% की वृद्धि होती है (सिंचाई दक्षता 30-40%) । [2] माइक्रो-स्पिनकर (सिंचाई दक्षता) का उपयोग करके सरसों की फसल के बीज की उपज 24% बढ़ जाती है [3]
- Answer (English): The mustard crop seed yield increases by 24% using micro-sprinkler (irrigation efficiency 60-70%) and by 18% using drip irrigation (irrigation efficiency 80- 90%) over check basin (irrigation efficiency 30-40%). [2] The mustard crop seed yield increases by 24% using micro-sprinkler (irrigation efficiency [3]
- [2] Strategies and technologies for enhancing rapeseed-mustard production (doc icar08, p. 3) https://icar.org.in/sites/default/files/inline-files/Strategies-and-technologies.pdf
- [3] Strategies and technologies for enhancing rapeseed-mustard production (doc icar08, p. 3) https://icar.org.in/sites/default/files/inline-files/Strategies-and-technologies.pdf
- Latency: 10.24 s

**Q (hi):** ड्रिप सिंचाई के क्या लाभ हैं?
- English query: What are the benefits of drip irrigation?
- Action: `answer` (in domain (best_sim=0.75))
- Answer: सिद्ध परिणामों से पता चलता है कि ड्रिप सिंचाई के लाभों में फसलों के लिए जितनी बार संभव हो उतनी बार सिंचाई शामिल है, सिंचाई से प्रेरित मिट्टी के वायुकरण से मुक्त, पौधों की कम बीमारी और पौधों की जड़ों की वृद्धि को प्रतिबंधित करना शामिल है। [1] सिद्ध परिणामों से पता चलता है कि ड्रिप सिंचाई के लाभ [2]
- Answer (English): Proven results reveal ed that the benefits of drip irrigation includes frequent irrigation to crop as far as practicable , free from irrigation induced soil aeration , less plant disease and restricted plant root growth. [1] Proven results reveal ed that the benefits of drip irrigation [2]
- [1] Low cost drip: cost effective and precision irrigation tool in Bt cotton (Tech Bulletin 25) (doc icar04, p. 6) https://cicr.org.in/wp-content/uploads/2026/04/TC_BL_25.pdf
- [2] Low cost drip: cost effective and precision irrigation tool in Bt cotton (Tech Bulletin 25) (doc icar04, p. 6) https://cicr.org.in/wp-content/uploads/2026/04/TC_BL_25.pdf
- Latency: 10.67 s

**Q (hi):** कपास में एंडोसल्फान कितना छिड़कें?
- English query: How much endosulfan should be sprayed on cotton?
- Action: `refuse` (dose for ['endosulfan'] not stated in any retrieved source)
- Answer: मैं एक कीटनाशक या रासायनिक खुराक नहीं दे सकता जो मेरे स्रोत दस्तावेजों में नहीं लिखा गया है। कृपया स्प्रे करने से पहले अपने स्थानीय कृषि अधिकारी से पूछें।
- Answer (English): I cannot give a pesticide or chemical dose that is not written in my source documents. Please ask your local agriculture officer before spraying.
- Latency: 1.02 s

**Q (ta):** கரும்புக்கு உரம் எப்போது இட வேண்டும்?
- English query: When should yeast be allowed to ferment? (sugarcane, fertilizer)
- Action: `answer` (in domain (best_sim=0.60))
- Answer: C:N விகிதம் C:N விகிதம் C:N விகிதம் C:N விகிதம் C:N விகிதம் C:N விகிதம் C:N விகிதம் C:N விகிதம் C:N விகிதம் C:N விகிதம் C:N விகிதம் C:N விகிதம் C:N விகிதம் C:N விகிதம் C:N விகிதம் C:N விகிதம் C:N விகிதம் C:N விகிதம் C:N விகிதம் C:N விகிதம் C:N விகிதம் C:N விகிதம் C:N விகிதம் C:N விகிதம் C:N விகிதம் C:N விகிதம் C:N விகிதம் C:N விகிதம் C:N விகிதம் C:N விகிதம் C:N விகிதம் C:N விகிதம் C:N விகிதம் C:N விகிதம் (| C:N ratio | 113:1 | 16:1 | 22:1 | | Distributed Setts in Field | Place the setts along the centre of the furrows | | Spray pre emergence herbicide on the 3rd day of planting (Atrazine 2 kg +500 ltr.) [5]
- Answer (English): | C:N ratio | 113:1 | 16:1 | 22:1 | | Distributed Setts in Field | Place the setts along the centre of the furrows | | Spray pre emergence herbicide on the 3rd day of planting (Atrazine 2 kg +500 ltr. [5]
- [5] TNAU Agritech: Sugarcane crop production (doc tn04, p. 1) https://agritech.tnau.ac.in/agriculture/sugarcrops_sugarcane.html
- Latency: 5.03 s

**Q (ta):** நிலக்கடலைக்கு ஜிப்சம் எப்போது இட வேண்டும்?
- English query: When should gypsum be placed on the mainland? (groundnut)
- Action: `answer` (in domain (best_sim=0.62))
- Answer: பருவகால பயிர் முதல் வசந்தகால பயிர் வரை 50 கிலோ இஞ்சி ஒரு ஏக்கருக்கு அறுவடை செய்யப்பட்டு, பயிரின் சல்பர் தேவையை பூர்த்தி செய்ய கரிப் பருவ பயிர் வரை விதைக்கப்படுகிறது. [4] உர விண்ணப்ப முறைஃ வசந்த காலத்தில் நைட்ரஜன், பாஸ்போரஸ் மற்றும் பொட்டாசியம் ஆகியவற்றை விதைக்கும் போது துளைத்து, இரண்டு சமமான பிரிவுகளாக, முதலில் விதைக்கும் போது மற்றும் இரண்டாவது பூவைத் தொடங்கும் கட்டத்தில் ஜீப்ஸம் பயன்படுத்தவும். (Method of fertilizer applicati on: In spring season, drill nitrogen, phosphorus and potassium at sowing and apply gypsum in two equal splits, first at sowing and second at flower initiation stage.) [5]
- Answer (English): inititate stage to spring season crop and 50 kg gypsum per acre at sowing to kharif season crop to meet sulphur need of the crop. [4] Method of fertilizer applicati on: In spring season, drill nitrogen, phosphorus and potassium at sowing and apply gypsum in two equal splits, first at sowing and second at flower initiation stage. [5]
- [4] Package of Practices for Crops of Punjab - Kharif (doc open11, p. 106) https://pau.edu/content/ccil/pf/pp_kharif.pdf
- [5] Package of Practices for Crops of Punjab - Kharif (doc open11, p. 106) https://pau.edu/content/ccil/pf/pp_kharif.pdf
- Latency: 5.86 s

**Q (ta):** வாழைக்கு சொட்டு நீர் பாசனத்தின் நன்மைகள் என்ன?
- English query: What Are the Benefits of Dropping Water on Cabbage? (banana, drip irrigation)
- Action: `answer` (in domain (best_sim=0.64))
- Answer: # பயிர் # நீர்ப்பாசன முறைகள் # நீர் தேவை # % நீர் சேமிப்பு # வருமானம் கிலோ ஹா-1% வருமானம் அதிகரிப்பு # தண்ணீர் பயன்பாட்டு செயல்திறன் # 97.00 # 45.00 # 87500 # 52.00 # 90.20 # மேற்பரப்பு # 176.00 # 57500 # 32.67 # சர்க்கரை கானை # 94.00 # 56.00 # 170000 # 33.00 # 180.85 # முளை # 215.00 # 128000 # 59.53 # திராட்சை # துளி # 27.80 # 48.00 # 32 500 ∙ 23.00 ∙ 116.90 ∙ ∙ ∙ மேற்பரப்பு ∙ 53.20 ∙ ∙ ∙ 26.400 ∙ ∙ 49.62 ∙ ஏரோபிக் அரிசி ∙ 74.30 ∙ 38.10 ∙ 4747 ∙ ∙ 6.39 ∙ (500 | 23.00 | 116.90 | | | Surface | 53.20 | - | 26400 | - | 49.62 | | Aerobic rice | Conventional aerobic rice | 74.30 | 38.10 | 4747 | - | 6.39 |) [5]
- Answer (English): | Crop | Methods of irrigation | Water requirement (cm) | % water saving | Yield kg ha-1 | % increase in yield | Water use efficiency (kg ha mm-1) | | Banana | Drip | 97.00 | 45.00 | 87500 | 52.00 | 90.20 | | | Surface | 176.00 | - | 57500 | - | 32.67 | | Sugarcane | Drip | 94.00 | 56.00 | 170000 | 33.00 | 180.85 | | | Furrow | 215.00 | - | 128000 | - | 59.53 | | Grapes | Drip | 27.80 | 48.00 | 32500 | 23.00 | 116.90 | | | Surface | 53.20 | - | 26400 | - | 49.62 | | Aerobic rice | Conventional aerobic rice | 74.30 | 38.10 | 4747 | - | 6.39 | [5]
- [5] TNAU Agritech: Drip irrigation (doc tn03, p. 1) https://agritech.tnau.ac.in/agriculture/agri_irrigationmgt_dripirrigation.html
- Latency: 4.73 s
