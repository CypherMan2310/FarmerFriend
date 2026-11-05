# CLI run

**Q (en):** At which stages should wheat be irrigated?
- English query: At which stages should wheat be irrigated?
- Action: `answer` (in domain (best_sim=0.71))
- Answer: The critical stages of wheat sowing are a) pan, b) booting and heading, c) flowering, and d) pan. [2] The critical stages are a. [2]
- [2] TNAU Agritech: Irrigation management in rice (doc tn01, p. 1) https://agritech.tnau.ac.in/agriculture/agri_irrigationmgt_cereals_rice.html
- Latency: 4.66 s

**Q (en):** What is the seed rate for direct seeded rice?
- English query: What is the seed rate for direct seeded rice?
- Action: `answer` (in domain (best_sim=0.65))
- Answer: • Method of sowing: Rice can be direct seeded by three methods: 1. [1] Preferably, use Lucky Seed Drill (which sow rice and spray pre-emergence herbicide simultaneously) for direct seeding. [1]
- [1] Package of Practices for Crops of Punjab - Kharif (doc open11, p. 33) https://pau.edu/content/ccil/pf/pp_kharif.pdf
- Latency: 2.11 s

**Q (en):** How much fertilizer should I apply?
- English query: How much fertilizer should I apply?
- Action: `clarify` (crop-specific advice requested but no crop named)
- Answer: Which crop is this for? If you can, also tell me your district or state and the season (kharif or rabi).
- Latency: 0.07 s

**Q (en):** Who won the cricket world cup in 2011?
- English query: Who won the cricket world cup in 2011?
- Action: `refuse` (out of domain (keywords=False, best_sim=0.42))
- Answer: I can only answer questions about crops, irrigation and fertilizers, based on agricultural advisory documents.
- Latency: 0.07 s

**Q (hi):** सरसों की उपज कैसे बढ़ाएं?
- English query: How to increase the yield of mustard?
- Action: `answer` (in domain (best_sim=0.68))
- Answer: जब फसल उचित चरण में उगती है तो उपज में 24% की वृद्धि होती है। [2]
- Answer (English): The yield increases by 24% when the crop is harvested at the proper stage. [2]
- [2] Strategies and technologies for enhancing rapeseed-mustard production (doc icar08, p. 3) https://icar.org.in/sites/default/files/inline-files/Strategies-and-technologies.pdf
- Latency: 2.86 s

**Q (hi):** ड्रिप सिंचाई के क्या लाभ हैं?
- English query: What are the benefits of drip irrigation?
- Action: `answer` (in domain (best_sim=0.75))
- Answer: सिद्ध परिणामों से पता चलता है कि ड्रिप सिंचाई के लाभों में फसलों के लिए जितनी बार संभव हो उतनी बार सिंचाई शामिल है, सिंचाई से प्रेरित मिट्टी के वायुकरण से मुक्त, पौधों की कम बीमारी और पौधों की जड़ों की वृद्धि को प्रतिबंधित करना शामिल है। [1] सिद्ध परिणामों से पता चलता है कि ड्रिप सिंचाई के लाभ [2]
- Answer (English): Proven results reveal ed that the benefits of drip irrigation includes frequent irrigation to crop as far as practicable , free from irrigation induced soil aeration , less plant disease and restricted plant root growth. [1] Proven results reveal ed that the benefits of drip irrigation [2]
- [1] Low cost drip: cost effective and precision irrigation tool in Bt cotton (Tech Bulletin 25) (doc icar04, p. 6) https://cicr.org.in/wp-content/uploads/2026/04/TC_BL_25.pdf
- [2] Low cost drip: cost effective and precision irrigation tool in Bt cotton (Tech Bulletin 25) (doc icar04, p. 6) https://cicr.org.in/wp-content/uploads/2026/04/TC_BL_25.pdf
- Latency: 5.18 s

**Q (hi):** कपास में एंडोसल्फान कितना छिड़कें?
- English query: How much endosulfan should be sprayed on cotton?
- Action: `refuse` (dose for ['endosulfan'] not stated in any retrieved source)
- Answer: मैं एक कीटनाशक या रासायनिक खुराक नहीं दे सकता जो मेरे स्रोत दस्तावेजों में नहीं लिखा गया है। कृपया स्प्रे करने से पहले अपने स्थानीय कृषि अधिकारी से पूछें।
- Answer (English): I cannot give a pesticide or chemical dose that is not written in my source documents. Please ask your local agriculture officer before spraying.
- Latency: 1.06 s

**Q (ta):** கரும்புக்கு உரம் எப்போது இட வேண்டும்?
- English query: When should yeast be allowed to ferment? (sugarcane, fertilizer)
- Action: `answer` (in domain (best_sim=0.60))
- Answer: கோடையில், கலவையை 3 நாட்கள் மற்றும் குளிர்காலத்தில் 7-8 நாட்கள் வேகவைக்க அனுமதிக்கப்படுகிறது. [2]
- Answer (English): In summer, the mixture is allowed to ferment for 3 days and in winter, for 7-8 days. [2]
- [2] Package of Practices for Crops of Punjab - Kharif (doc open11, p. 146) https://pau.edu/content/ccil/pf/pp_kharif.pdf
- Latency: 5.63 s

**Q (ta):** நிலக்கடலைக்கு ஜிப்சம் எப்போது இட வேண்டும்?
- English query: When should gypsum be placed on the mainland? (groundnut)
- Action: `answer` (in domain (best_sim=0.62))
- Answer: மிளகு மண்ணில் வைக்கப்பட வேண்டும். [1] அடுத்த பயிரில் மிளகாயைப் பயன்படுத்துகிறீர்களா? [3]
- Answer (English): The gypsum must be placed in the soil. [1] Gypsum is applied to the next crop? [3]
- [1] TNAU Agritech (Tamil): Groundnut crop production (doc tn07, p. 1) https://agritech.tnau.ac.in/ta/Agriculture/oilseeds_groundnut_ta.html
- [3] Package of Practices for Crops of Punjab - Kharif (doc open11, p. 164) https://pau.edu/content/ccil/pf/pp_kharif.pdf
- Latency: 4.31 s

**Q (ta):** வாழைக்கு சொட்டு நீர் பாசனத்தின் நன்மைகள் என்ன?
- English query: What Are the Benefits of Dropping Water on Cabbage? (banana, drip irrigation)
- Action: `answer` (in domain (best_sim=0.64))
- Answer: சொட்டு நீர்ப்பாசனத்தின் SALIENT அம்சங்கள் என்ன? [3] ஊட்டச்சத்து செயல்திறனை அதிகரிப்பதற்கான முதன்மை காரணிகள் வேர் மண்டலத்தில் ஈரப்பதம் மற்றும் ஊட்டச்சத்து நேரத்தை மேம்படுத்துதல் ஆகியவற்றின் அளவுகள் குறைந்துள்ளன. [4]
- Answer (English): What is the SALIENT features of drip irrigation? [3] The primary factors for increased efficiency of fertilization are decreased quantities of applied to the root zone al mo moisturing and improved timing of fertilization. [4]
- [3] TNAU Agritech: Drip irrigation (doc tn03, p. 1) https://agritech.tnau.ac.in/agriculture/agri_irrigationmgt_dripirrigation.html
- [4] Low cost drip: cost effective and precision irrigation tool in Bt cotton (Tech Bulletin 25) (doc icar04, p. 7) https://cicr.org.in/wp-content/uploads/2026/04/TC_BL_25.pdf
- Latency: 6.92 s
