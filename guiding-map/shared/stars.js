/* SecuRAX real sky data, read by shared/sky.js (the night layer). Generated from the catalogue; do not edit by hand.
   Stars: the Yale Bright Star Catalogue, 5th revised edition (Hoffleit & Warren 1991, public domain; bsc5.dat from the
   Harvard-Smithsonian CfA catalog server), every star to V 5.3 (2319 stars), brightest first. Each star is
   7 characters of a 64-letter alphabet, 42 bits: RA (J2000) 14 bits, Dec 13 bits, V magnitude 8 bits ((V+2)*30) and
   B-V 7 bits ((B-V+0.5)*50): about 0.02 deg and 0.03 mag of rounding.
   Constellations: SecuRAX's own stick figures (public domain), drawn by Bayer letter, stored as pairs of star indices. */
(function () {
  if (typeof window === "undefined" || window.SXStars) return;
  window.SXStars = { n: 2319, pleiades: 145,
    d: "SAmg4gZRETURMgmCJtB3WnGCl548xpLch6ZOE8Fp9BN-3RSAYUaodqOuEWC6aURPyYqKX2lgSoicO07IyamkMQ5d6tmr-Vpqz0jyXAiyOUrqfa9L" +
      "9O1Xi-eiHysbEO3LcBjEehLyZDINnGCl7JFbCpEDIUSm1bLSPhYy7Lbou1Es7aOOc4kDaOOgKircSYlhzbcZO8X5LeQhLyZDgM7CD07gSiZ8-TiY" +
      "VwjyriOJFcbjkxdgNfTlOTClpzm7xE08boYWVStbpZkyMYjoQu_kLbotP-7_rqas1B3TthRrZdTsZ2eS9TsPXUjIzubRAmZzuOUNK1buaZOnOrvh" +
      "Fp6FbxSqpaTbweGv_7zy3ydVqbyOB8GZrzMPJX070PAX6lb0UDGbKj1oPdXI70QloUxD1Mnlulz1iu45Hb0g8kD1T3pIXbo74WfhJS74eh2Dpj6Y" +
      "2Urk787YW0I79sBzdBj_UOwX-T-Opi6X7-Yv2ck7_lVfkccAMYwiu0AiFgrw0BeAaNQcAqju84cAas5U88DSkcDP0COnMjycCPm6UQMCQqrl_UET" +
      "datAsGYBK0PUJQ5944MJmvOUh8IO9gKfsLsty2mkKcfusxcKZ409j8KkTvVZUMV3Y7BMNMChdZUMS9jJWcOXY_DHEOQIGoXURrlIzzEQOd9p0sSf" +
      "sUXD8SaOymakSkgtGcMUUgXzfcUTyyFWEUdbjpw0VSowXKsUUP_bTsWVq6WPUWWFGJ2UWgPGE-MWThh168ZGp-IkkZUD0NWsYglGZosY2n70KsYO" +
      "NM68sbmcvzm8bGhpx2saPus0r0aOTbks8bqnVaaEbKw71WUbe0uY8UdlrTnq8dorvNd8dGjlUvMcbnmGk0cgckyRseOO6HeceNsA56MfIvRIZ8fT" +
      "pkEV0ePNr3jEggusMpkhKBJRIkg4grCx0gOVq110gusgKz0g5xPlvchNsQ1fkiMAl5WUiOiw4-UjIOl2J8jCKaK1UkfqcyXMkoudTEMliFRyh0kn" +
      "7fSpMleKHKJEkU0qsAskY6F2kUkoRBaAElrUNK1ckbKkrjkmQo1x5UmZqnlrcmQrnFucmgzGmIcmqT4IvMmUifbZ8mT5Z3gUnCIN8wUo8SODgEpV" +
      "8lKr8pEKlGzMpohVGiEoWuwDkUoQ67H-MrKR9KO8rfaCqHMrBNbL5Us0wQlS8tLy6JO0saFwrHEsgPAp4UsQgc1_Utcjgl8MtHJ6MP0sSaGCN0sn" +
      "dw79EtS6ZkrcsTQ51U8uQSzV4cuVmwrZ8uivc0b0uyGMXvEvgk30OcuQbqbsExoiDx8kwQo7OYkwczOuA0xLs-UnkwP0CKfExS2RGr8xAXzIh0zL" +
      "c32j8zYwyUu8zn3ATy8zLPmU0k1TY8LDs1mZYy7k1me7CZk0Xn9kQk0PtRjBk1pX98RU0iuAKNU0duAbRc3hNn7qk2QRrkKU2UZdsl82wtud102T" +
      "yB1mc2UM4onk4wNk2As5inOSOc4ltO41U5S4k6r85KvjUtU5U_Fe5k5Mo80Y06O11n7U6W5RuRU6OH7Eas6gKGRZs7qre3lU7Jyn6586WT90Js9k" +
      "w8nvk9IBv6vk9ZMLTG88USJCfs8klnloM9RuUFx08O9GGmE8cQqaAE9poLlwM_upHNPc_TC8D2U_GN6Gj0-UgsNEc-dbRxxlAVcFyhFAUy-lilBU" +
      "t4EKFAtU3FylBXd95X1AYudi_VASv9XIdBKLTyctBG7JtLFBoObHyVCQSA5JVCuWrtZdDDzzYRtCpkNX8lCepAkB1CQFFtqNCSXaoklC7ieYTVDo" +
      "IO7c9FsL8ZaVEibbSjNFm8go9lEUD7UJlFoFB6oVEyk3kS1EOojDXtFHqrEllEOvZqdtG-3VSHdGh3Wdf1HHCL9I1G1YfSwlGQbaaFNGoy8nkNGU" +
      "DDHGFJTbbb0FIayOq91IZHQoSdIeKspHFITSvlhFJwVMTStIQosK9lJI1R5u9JoeKK8NJft_JR1Jh85KL9JI80zcFKdEoGlVK9oFrltLKxMz6lKQ" +
      "ykWH9LUWEY0NNjZ1I4VMya_pfVMY84N4lNOL8JtFNMTkJ9FMqqNXsdMXsk7ddNH7H4jVMdJ7HIdNHO5Y4lMQahzJlMVezVK1NIvAWodMmPbGrtMe" +
      "mMj6FMQA3XN1PWGETa9OTLdk_tOTeMWr9PRo-ExtPm1uSHlO_EW8UlPZUpKK1PIs_kntOPw8OdtOy2I24tPITeZeFOemv6s1PappVf9Peg8yodRg" +
      "DvHRdROJGozVRGOHnZFQUPT2AVQwSWbBNQeYKcMNQZZXUZ1QrUrkoFRwbI25tRMfloKFQ0EEZXVTKXIDS9SQixBpFTUtGEPFTeutym1SUvXiP1TU" +
      "9a7w1SUHjqbFSUKL6I1SU3AZTFSvfXCEdShLjJY9VKh2n31Urlh9uNUW3xSzlVYBpcylUPpuFWlUQwSzjFUV9wWHlVWZZ9mtUqqDpXtUcXRVDNUQ" +
      "h2n31U3pPallUn5yGhNUpI3mENXqM8Yf9WQaAycdXW-GYStXHFJzadXEJ_6JNWUv56mVXIP12vdWqfYcP1XUqQoZdWg1IIkdXENFIN9YQP-801ZL" +
      "nZIK1YY4OL51Zs4qLYdYsE9HFNZSJd3KNZFU_UZNZNwVI2dYfJNY3VYU5L2AlZL9AXU9ZrNcrptZWYLz0FZVrpJs9YmvdoPdYbvttDlZU799MVY3" +
      "Hls99btLsJj1bKO1CclbCs4SwNbo52BH1bL6-qQNavKAryNauWeiH1bSy4GEVbMzbcvlbJ3GJalaW3dHJ9aZ8D8eFaaTDhu9bNdCyxNbIS2Z1FdA" +
      "Tz6eFdMz_cmNcg18MJ1dZIbL_NdKaRNP1cobjpw1c3pjI79cmpjI79cmvFsFtcQPDnxNcNPnWJNdKb1GgNdjMP1SNfKY1rRVecb6Cx9eosCoLVea" +
      "0xppdfg_AcIVfMJ-K3tecdCbClfNlQkQlePndg-dfgwVqjleY0z-PtfGL8Ja1fIXJD2te8XyCnFeUcUztteoeu-KVfqp5qVleZxDp71fU7oX4FeW" +
      "J9yPVhSPbzdlgiQ_FB1hFTU1ntgQbUkQdgccII09gSqgpZFgxrWiVthQxkXRFhcLSkPdhQhrTr9gcv1bT9hcwnWINgkChra9ggIiVbFgzKCaKlgW" +
      "MXWuthQOuE2NhSSaF2dhwhcRltgShfeM9gSlRkBNgPoiDq1gWAaz71hMYo4NNgWaWKT9hWkDEf1hUnP3f1gsqh1Z1gPH13NdjQeRDKFiSg4n8Nia" +
      "ri8HdiSsJw_NjG1K7HljMWeXp1iY1AIFtjG9yz-tjMKz4iFiaXYT6FiZZxX5djbdtywljWhPziViQplGr1jMDCjF1kVtWav9kY4tId1k0MSHs9kP" +
      "UgHJtlMzoWadkkBKkHlkiXUpnVlPeZo79kt34LqNkaEDjo1lKHv8sFk-RoWSdlOUhhjFlNju84dkgqRFAtkX8vKGFlOLvE-lnkP9kMdnSSN1HFmO" +
      "UnVbVmighTWFmSq-GKdmX1XBhVmYPn7etnSXHk3NnIYB7ttmvYgCdlmQwB4QtmazukY9mU7-EIlnM-W2NtnQFfOb9mYQqXcVnbTah9dnA2BcPdnl" +
      "-HC0totFVWIFpoHujkNp_YHCGVogbwBa9oqnM0pFoQGGrAloaXlFidpYjys41ohqwNNNozrM2RVobx6hptpSzrEDFoU2pKstot832ytpo_-InFou" +
      "MsHtdqSXaajlrMgYFzVqprjDitrPyppVtrPyvnfVrQ5g8DVrG8PX_VqUNfNX1rHfX4lNrkibS61qQwPoONrE2z5AVqSKn7LlqaLDcPdqYLMnZFqq" +
      "g0iT9qQydr59roIZ8aNs2eRoiVsWmP0olsYmdMm9synBDm1sSnRk39tcoZT-dsQCG6KFtRUQ6Y9tmtUTRltiEm8gVsXHF4B1sONLJM1tSSaW7ltg" +
      "WKBKdssXT0NdtEk3pZ1tloxyxlse4RGd9sYZiCvFsadU2X9tQecGbdskmDHd1sz4-5wttQ579OVt_ETbrlu0GTR5duaIG15luhO-Y01vIqK5nNvq" +
      "HJEdVvMHGB7tuWJX5JlvRU2z4NuQcPhA1vofZykFvGgyB9dvopoiG1vUzFkodubzHUgNvV3o1m9vr7_UHNvoHTMYFwyQG429whS1WnFwTaSmrlxH" +
      "gO4xtxK9XzT9xKxSDo9xM1H0R1xP5_KR1wu7YLWtxi_HIgFwyLVMTVxIOZnTlxJXAkLdwepd6ydwS3YlwVwu_Ib8NwVRSpy9wSTMn9NwYgTiQdwq" +
      "qZGg1xMqj6Y9xW8twxFwjBd9l9ygQL6EVzCXAogdyZsSU3dzo7anTtzKKM0yFzIugV2dyn8eVmNyUKD6INyWT9q01ypmEMGNydk3U8F1kl6HFl1c" +
      "yCJ010w7VtEd0n8vpFN0yOtIh10SVMl9109sL7xd0YJS9U90tPJX0903b6LQ11G9J1G91K-CnMV1QLy5-12gw7OV12UyGXk93QyUieV2S2ptmV2j" +
      "3Xaut3O5LSMN2y9-Hdl3nA5CO922HlbZ92qJn8SN2WKFV712ukslEF2sq9kut2QsEE6l2RstvSt3G06q7N304xrgF2f6FMYd2TVCTud2SslRHF3O" +
      "2Hm413ODDvqt5WDF8Mt4WGiDwt4SHS2xN4SLYTbN4oMTLqt5WMQI514iWWb1t5mX75Dd4gb4FPV5imj-ul5hEr40F5JP_8FV5vg0Q814ThgLrN42" +
      "jMqel41laII14erDr_l4WvLW214dHVY5l4oI40LF48JgGE94UMXZHN4fNvXON4QVwTyt4OiYEbd4ki-TkF4Qo0zvt4V3aJbt5N69GxF4WCzIs95J" +
      "GlowF4WJpICV42L1qB14mMi6Cl4SUl6kV5RcajDt5Nfr0_F4UsDWhl5H4_WgN5G9pEId4u-lIkV5OK9sed6aLW4yl6WLzZl96cNEt5V6aONG1F6M" +
      "ZpvOl7jujVWF6tu9UkN7Qzs0BN6q6Bdbt6z61tvl6q7HK8t6w8EVIF6a_B72F6UKAqLN6UXQYTV6Pe-n7V7LybLR97t17tB16eCm1ZF6RZaaCt7m" +
      "hbWj16spF7Ul6oMd2QF9qT64y19gXZWy99GfiyVN8SmiAkF9anoUIN8Sp9e6l8bq_2JV9D3Cn5t9IDKc5t8iFbYPt8aRal618NXIysF8UgIiX18m" +
      "iXDpl9emPS_V8fpsUN19guQm298aw4rNN9UVt3vF9KYuC4t9qlaT8l83oy1Ul9Qug4Xl9k5_1EN8W5-pit9UH7Eat8dIhJwN9MPUyKF8kQr6n19M" +
      "SjNMV9EVsB5t8UWQBHV9TZoznV8imfz918uwYiV18kBpK_1-SB7S5N-ZJXMRF_cK4J9l_OM64yt-aN7G2d-UP5E3V-QXfIhN-XhMqg1_SlmkV1-Q" +
      "wZJ2d-RuxPsl-axCCiN_jx_bV9-iyF5nd-gzZbY9_Y0TH4t-V7-8PV_tBZyZ9-WBt6mt_EF6YyV_GQvE4F_LSf2e9-WbBY41_i0c5md_A0fpjd_O" +
      "1Uk3V-S-zEo9-UOxJp1__jHHgd-YtEY51-VNBHg-AmRjjSuAYVb4NWBYdV0P2AeuRGH-AszR7euAS1uu6GAW44jP-Ai-IXL2AS-fmKmBiSNzO-BH" +
      "TgFyGASVvGSmASoIYL-BN6kzHOAn-dqFOA3FDT4mBoO4o1-ARPwJzWA2TKasGBYVQTn-AQeJKzWA2nklg-Bfus6UmBhv76ruAs9r-s2BB-LFG-BS" +
      "AFnd2BqCi6FODIKDW7ODqQVpUGCQdcJy2CcmW0fOCQmyDg-CQr3mXGCn3dHjeDs783_-CsCKorODkLWHUeDCRr2YWDSnKpOGCcqEIp2C32Za3GDc" +
      "3RJVuCp4zLGmCU7t8pGDMAp2UWDsEgofODdLZiuuDPRDoaGCiV9UaeDUXDoTGDWyiCBmC8z8aMWDkMeER2EqN4W8eEUULmBOEyV10euFqWKEveEk" +
      "YAUVWE5cQC4mFqctA12EQsGGF-EgwFIHeEazXOhWFY0L4p-FUHhFHuFKN7YQWFUZGaU-FWfmz_GFam4KpOEr68EfGFe8eL72Fc9AFE-EXHV2WWEx" +
      "I56lOFmKM90uF3NNsx2EYNRYJ2FfSIYNuFQeE3rOEkgXDf2ESr4DxeEW9oV4-FGQiJQ2EQQ39PuEaRQFGuEQYZclmEmYOxjGE3a_7IeEid2l-OEa" +
      "0ScduEs74iOeEYL1pY2GmR9JLOHTTOj2GGpVAki-GQXaS9GGQbBX9-GXn4HnWGp4pY4-Gy7Sbh-He_O2tWGXRdopuGZUZFnmGQUzlseGWZjMoGGa" +
      "bmTBOGTdI6M2GakxJjWGxrvWOGHM4UVx2Hq7ClEWGc_NIKGGj__yK-GVDL6rOHQHdqmWHQKtSeeHsMKFWuHKPjDAmHQZTUzmHhpCiumGi1deCGHb" +
      "3SjYuGm3WdHmG04bW_WHI5R2D-HG8Br1WGUA0bROIcGoN_eIfPhbe2JIZwCjOIWmL2z-Igp2Zv-IbuY7TWIY1M1leJi2CaeOJY9pY1mJo95MZGIo" +
      "CN7puISHn7HeJnQAXumJWUVE5GIUfd5zGI0jrClGISjvCQ-JEwgD6mJM3cbPmIU9gYVuITBZyZ2IgB_cSuIWFbOTWIhJVNO-I1OJK92JYRj19WIW" +
      "T_pEWJZl78mmIjoM6ZWJXoi2PeIVpB0uWISpmEAWIQuhHjGIsvclhuJB_wNHGJWNh02OJVSq-12JdZhbPGJHnnpsuI_rlV2mJD4S8PGJo-oZImJI" +
      "AK2deIWKnCiuLqYSrauLNZiONOLAk-FEWKSmfz-2KS53eVuLQPE4XeKUZbH5WKebijG-LqcmineLurzJP2KZwXFeOLI5VaGeLq7msIuKU7wsZeKe" +
      "_glf-KaJpka-LNPtKdGKYYXFs-LoaTD3OLVvMuaeKu1C6I-KW1dFieLsB1j52NKJ50r2NVOh4RmMPO6HkeMQUmleeNqaUczmMaqYlv-MWrN1hOMR" +
      "u6z3eMYyb6A2NAzCkZuNQzlt12Ma3pqaONC783_-M3RSHX-MUXH9t-NUZTHwWMwa5W1uMUdMEs2NMd5So-M0jNirOMVnWJgeNKn5d3GNopIEjuMZ" +
      "0TFyeMW-QKHGMiAPXfmNNAwrcGMcLeseGMbVVGXWMddoCc-NMzomlOMe217ImNpFDISOPIOwXWeOMUZFnmO3XRnW2PDYs0rOOwe4TLWOVibivmOS" +
      "phXG2PMqV7xeO1vBHR2OewBXrGOsygIX-OiChdQuPJH955eObH955eObIgLhWPQKPeV2OaQLZymOnVBjl2OOdjopuOqeAqDWPsqNKUWPBq0y3WOl" +
      "r53QeOi8VMlOOlNeZ62OhTZ1hePpT28X-OYUPVeuOUhxkcmOVp1UB-OtqRFtmOWwA4Y2OYwU4xuPJxZSduOUxfUPWPM1Yqd2OiDR6L2RNKY1z-QS" +
      "MLJUeQmNG45uQePvSZOROSbpK-QoUCFP-RIiEC-uQRkvTbeRJk9NwORoqzzn-RHs4nCuQwuHrUGQcwzVmORs9hccuRODLZ3uRMHRKdmQSKql3eQS" +
      "R0o4WQMTTVqGQQTe0vGQUXQp6GQab4i4OQycZCvWRjgColmQghv3SmRWh5TqWRQkes3GRryR9R2RUz2IB-Q37yoH2QY_5qPGRoE33DOQqJTsZmQU" +
      "QRmrGQcYfNpWQqpxE8WRKwAZfWRY4D1ImRG538jOQTNiZXmQWSeWNeQsVY34GRkZtoaeRbrkhAWRuxDXNORI0G-MORA255TeQe5pmRWQQFHB_OTI" +
      "FiFZWSQL2ZTuTKMapamSgX1jUGSTZCFb-THZN2A-TSiBylOTOkFnceTqwOVXuTA0a6rmTK4do5uSm5rnTWSi60S8-TO60HzuSW8m2U-Te9xmAWS5" +
      "H8rhmScH_YyuSTUXlvuSUarYt2Tpe93IOSVfH06WSWkM8W2SfxTGtOSc1JlqeS-ELdQ-TLGecd-TmLVLmWTMOL7kGS4OPmHOSWOqH52ToU0T0OTO" +
      "YQBu2SScY61-TCdEb1uSWi8jsWSSlOyVuTQ1FIwOTO4zFI-Sc9Fvf2Tg-0GJGSa-5ENmSdJTiZ-UtNlC5GUzV1m2eVIY9VsWVqfeiD-VmgMSYuUV" +
      "oOj0WUSq9T_GUkx4XMmUqBas2OUUJXHjOUUKKUqGUYOTX92UQfU2XmVKjcrm2UolCFKeUStEUPGUyuEn9eVS3rHM-Up5r9hOUo55WUuVF59qjeUx" +
      "D0uDmVONAJRGV1PmrUOVqb0rAOUmcBBmeUbdanx2Vqg7JlOVMjfGX2U8k-LD-Vsp3WQGVo0FLD-US3_sOWUW8x_Y-VY_BD9OUdFDJtuUXGwmpWUw" +
      "HGkMGUcHmmImVGHlBVGVcV10LeUicJbl-UklxjQGVImDckOUjp5k6mUSyzkQmUY-KeDeVDB93DuXMDiKbGWaIP9CmXMOyq3GWqTUTteWUVvCjWWu" +
      "YHeAuXmj42lOXQoK8PGW5qR53WXmqy8F2WUrEbPmXMv_l4mWX2QG3eWW26ineWn9pqQ2XcBZTqeWaCW35eXoSG4tuXfXKjy2WfZ1l52WTernu-Xm" +
      "mQT--WomXFiOXaq3G_WWwvITm-Wtxc9EeW3zY55uWW1fkoOXgMBpcGWiNArQ2XgO5Hd2WMPqoKmXeV70z2WUeL7ZOWfinpjGXnre1dOWauUB-mXW" +
      "2A6RmWQ2nmauWs3s78eWSAEhJuXYFPqGOYnKanvOZINVW4uYmRwLxuZWTaF7eZuVO1TeYgY4W7-ZIZ91iGYybi5u2YwianJuZpsAlxOYUyBSO-Yj" +
      "7GubeZH7XEU2ZB76IauZO8hqmuYYAppy-ZoB38fWYUItHN2YkKDNoWZBLvZjOYgPEHW-YgQ1uKWYaYdt9-YyY6XJuZIhEclWZEi_KdOZjjWB92YV" +
      "jc4fGZsu-uHGYu_7skWZ0BPlEOZrNZnXOYQQdTHWYOY7idGZIZj7hWZKhAKTGYyhjaAuYZmIrJ-ZOmlnzWY8nQ6W-ZsoGKOWZkuu13uYZvkEb-Ym" +
      "xIGLOZa2ILYWYu7nahOYZ8IifeZqCXNbua0FtrXWafI1bCubkNxJYuapP6aTuaWRv2vmbkVWSWeaQWVjsOaScVmz2b_ciyRWaScoSUOaShLjbWaS" +
      "kVbOeakluu5GbdoOj0Wa3okkC2aQqR7K2bLrpoF2aqs28FmaetYXn-bjuGq8WaQxKN0-bUya-VmbS3DJ4maY47EX2aa8B3DWaW_MWaubCCctPebW" +
      "D5cCWauFDJt2a3FNTyebFF7L7mbjI3ITOa7OHE5mbLN8iB2bZSYWM-aPTD0eeaQWSVD-biYuMzWaibqUTGbRebXCObnlzKOua0nKpOGa3qxaBuad" +
      "sfNvebWvhVLuaXyDKXubVyaF-mbgyiXeubP1SVq-bG17cKWaeEAoi-beFgrw2aaHF28eawHXB_eacI491eaSLSY0ubBUbEmGaQVtsk-accB8-eaz" +
      "cOuuubJdXIUmbTsHpBWbk3gsGWat4MmPGai664c2bhFL1_2dgLoMIecYT_l9GckcwCR2cSfWYu-cii0zmWcajNEo-c8rpqvudKsrtC-cszW1wWc1" +
      "8mkUedM8sjPudU9odR-cY-H8W2dsDXh4OcwG7of2dEN7ra-ciPK5eGcSPg6LudMW5y2GdLXODR-cQbEDZWcThLiY-cTmNpc2dWnL4uedLoySWOdY" +
      "v20D2dWw7YTOdG0umPmdI_8Xr2dIGF7Cuc3IiOnOcaLTnFudUPsk_ucSSDtSGcdeJKzWc3jbyEGdktjE9-cmuxM52cnvQ2Eucwx-E1WcQymTS2cW" +
      "ynEs-ct_bdNmdQDqcC-dPI0V_-dGM47VOdhOkJ82cSUt5pWdiXMGlWdOaaVsedWh3Y6Oceqlmu2cUuw85-cmv50Suds3ASiGcu8abeOcP_9c9OcW" +
      "AgGoGeyCLMh-eUGfW6GeYIqp3ueYTQT--eYXGVX2fGXzVimeecEDOeeycUlkGfqq0UkeeStKNyeex0orUefI293xefp3iD5GflDzms-fWG1lfeeW" +
      "Q43vWfpSkMAmeaTL7fufiUaLEuetfoyNGeUiXp42fGirqvGfUsZMWWfmx73Q-fR0OzuefQ3jk_2fL5jLbOfP9H4yOeZHNrkue2MFX_2fbNZmN-eW" +
      "POYIefUPiZH-eWRG8YWf7cYmgGfHfZ0Zme6f_BDGeWiQU-meXk4J4-fgl0WjWfvmJQzOemoplMuesr7xxWe0tk5Ieef2p3vmfS3VKPufU6hdp-fy" +
      "-q9NGeTTH3n-hMX3ivGgQjTSv2gxjR7kehOmVyzehEnVU32gaoC3PmgZq6WPWgYyXsgehG1JMqWgf3brDmhb7HlG2gxH9bIOhWLJkROgqLk7EmhI" +
      "QOWiOglRtztuhES1zl-ggVUnrGhWXjD-WgccDBfmhth3SsegXis9AmgroU6Neguyq622hiy9EtOgz1wbRmgS_SqnGhIB78LegiEeLm2gUF4qsWhA" +
      "Lb51GgmNTbXmgbOMZ9uhIUQDVOhfUdmpOhnVfaeGhRYskkmhQZ4V3-g0acGT2hodklkugrfJye2hShi-OWhaiTKcug6kL4U2ganJZdegYnYVvWgq" +
      "nmny-hKpE3FWgvrRDJWhNrM3G2gesLkFegc1Jra-gV1qTTOhq8-72Whn-iIHOgaAM3EOhqEhryeg4I9L2egbLkqbmhSOb4KmgPPJn5mgPQFXDugT" +
      "QiZb2gSSgDq2huek4QOhLguqIOhKhLKbGgmhV-JuhqjEl8mhOqks3egmrcuu-gsw558-ho0TnYGgZ08KAmgS1-JWegd2q8WegU9Lca-hy_YcIGhQ" +
      "DVz9Gi2UDPU2jsTqGT2iXg6IS2jTpyl4mjcpZe3-joshGbGjQwEZ62ifxaT62iUzc2UOjM1J9OujoJ4rBOiYKuSkmjgL7pdGjSPzUs2jQUK2tejg" +
      "VC6YOieYRIc-jWZa5AWjObvd0-iWfjhwmjfj_V7mjpk4mY2jOmllYOiWwh6yujszvaoeiU1-7RWigDj9LOi7Ear8ejGFwaTmiqJP8XGiUQzNd-j0" +
      "Tf10WiSXHW5Gjgj7pOei8kN7TmitteZQOjpwhV5OjOxENOeidygIX-ij-LXJWiY-cNiWjt-2KyOjeEkXrGleFKOGukUH8iTmkgObrUulgOa5i-k0" +
      "Pxc82kcSQ08mleSzHn-kPTzo02lMUlNN-kdV7WmOlOWpUBmkRbsCDekSdXoiukheWb3WlKiAcCel_qpUSmlLqu6p2kWrbDjOlByc1_Glcy9EtOkz" +
      "zSdIOlT0u6_2kw1h1JulW7C0-WljJ4VKWkRKitbmliNoclekqNqpqGk5OWYUOkSSfmwGlUTQ5b-lsYfkA2kkZp4m-lOcleI-leeXUyWligvK8GlS" +
      "g2DGWlohM6Ymkdo_Dvekyq0Vs2lWrB5g-lIr6eHOkWuPJmulqwVb3OlG0NJwekU02Js-ke40r5-kY9VtD-lg_GmvGkl_5SSWkcGWhdGlQMZW7Gkd" +
      "Qs2x-kVQgCK-lqT_qe2lQU_U6mkvW4Dj-lcZemH-lMZhTcekQkhjJukWkhHOelqlLqcelgl4YNukTyu8K-kizlHhOlH3wqfmlj5pLl-ki6H1QOkb" +
      "7n5FekSAG1W-kSNblqmnOOBa5-mkQVksGmUR6r9WnjSQrtunYcIj0unNhJrd-nJhkJomnSow-YmnepYLoWnoparoumdrzl6umlvhMg2max_oLumW" +
      "1Pmn-mc4mBxGnoAdcGGmtDBr5-meFoKA2meGLai-mbIuMhunSI2sc-mWKjdm2mUL85KOmkM5mj2nKNjjl-nkOObBOmmP9XJumiTakv2mQTtqOenG" +
      "dJa-mnQfRCcmnBnr0o-mRqX2NWmYta1JOmUuKY92nmwntuWmszyl0mmk0CHwOnw068tenZ6ougWmv8WHn-nSEtzPmmbFcM1-mVQJVqencQu5F2mu" +
      "UtWtOmqezFPOnogNhMunkjNGj2mwr8buOnls-KMWnYviO12mywUKt2mzx5c7-mU3DKJOmS3j76mmj6N6rumY7LtR-mm_ZYT2n__duBumYMcct-pO" +
      "MiUsuosOVvCuowQUCeepYQh3auoPTfsZWodT-Kf-oeUbJkmpnVoT-mpkXE1_Go-aVXR-obdT7l-o3jyBWGpQuweDmpPw9cXepszrzKeoa1ZcdGpQ" +
      "3E45Wo93nzaepS-PYempVBP5l2psIkX5Oo1K3dQeoyOTVzGo6QYx4eoVRPnk-oQSmU9-oRUkz_GpAZy2ueoSj-Tc-odmVA4WoUo3IKGo0wRZ-epo" +
      "x-Lhuoh0jmkWoq0e8C-ot-FXUGpp_Q462ptCLZgWoyCKRV2peKJY_eoSMCkAWoQMaJZ2ogNWfN2pZOBVmuoUOkLEGpfSHnM2pzUePu-pqWJiK2pS" +
      "ZbI3Wpel_y7WoVpwLQeoTq3G_Wo3uBFoupExbD7uoS1pKGWoQBm80GoUNm9PeoVObH6-pJO6HhOoUUxkk-oUV9ExeoQaOD72oUa8TympFcLl4-pp" +
      "cN4nmpIcSCtOpUcmaD-obdX7fGolem0NWoYl51k-pTsR8tGoXtz0CmpEtwrn-pZyjGKmog6Xmy-os6XKTeoQ8Qui-os8oLt-pJ-L2zepB-XJGGpa" +
      "_q5s2ppBdCZeqbJA51-rXJVc7eqcKMKJWqVQdRW2q9VN0FGqQWjzSGqmaKcF2q4cA38eqSeX2VOquj1Ed2rVowSlWqWqdx52rSy-o--qW6AHMWrQ" +
      "FN5lWrHJ4NnmrqLHfLGq1M85rOqkRf35GqSTRUCGrnTpJ0WrlT1zd2rOXlT3WqPdDM2erdgtpUuqcja1M2rJmaYhGqfwZZyGqgw_kkGrkyb2nOqi" +
      "zfoGOrS1kJxurO3HWY2rs5woM2rN7jw2eri7ZkTOrH9c7zOqeAFXu2qTFFUOWqWH4a1uqYIKSsOqqKNK8OqdKYk6eqSMMHROruPjSDeqSTf0u-qR" +
      "VS17erRZKzQWqUZggzmqSeXyOmqVfgFn2rpn2ya-qZpkbd-rrqR3ueqfuBFourE0CafGqU0747Oq0210C2rM3fUF2qq5yb2Orp65diWqd9fU6Wqo" +
      "_pgterHApXTutqA-GN-t0D-2E-saLuo12sdNonlmsWNuXmusvSY-H2sSVj5KmsaYukEOtsZgDpWsTciN12tViE5eWtcmX4wGsYnVaaGs3qh0-2sf" +
      "quZlWtKuQ6LWsYuaUE2sWvgaRutTw76kOsjxFLgusazMNDetM0OnD-tS06rcWtu3HSnms09woxWtiBor9GtpDT3S-swO53hWsaS1I-WteTpbRGtP" +
      "UU3omsvV8D0usSWfIrGtIYo9des2dtyfuskevyt-tPhl0Wuskop9_Gs0rKFYutRsviCWsVx8kmGsezE-zeso1aSuWtm7oGFOtO_9DT-tSFaUButk" +
      "GlE_useJWpAesYOgSw-tLQJ5wGsUQyWgWtaSROAWsQSOD22swStDbmtqTJTputXUx6-GtpU94KGsTWOqa2swYX98etkYap9etKakLpmswgi-5esq" +
      "g7my2tOmNHzGtMrWDymsSxZmXWsZxj3BmtHx-bhWsiymypmte1CdHOsS3aJbusy678AGtoGw7NmtiI1MdusWRZW5mtYXpL4utKdqENesaevytesy" +
      "e-ijetRfBygWsYgKkOustg_B_-sijesamsWkwUx2sYlGX3etPlRFx-sUnlmlGstoPUWetMpilgetastIw2tmvTDZOs8zR4NGsWz1LOmsT2BqFutN" +
      "3MyEWsW4NhJ2syDKayuukDdYUmudHBueOvFWAyaGueXRjkmuPX-Sv-uubRCGeukcO9EuuqiiTc2uWot0T-u2vtLjmvUv9lT-vyxcEeOudy8zWWu0" +
      "zx5D-vAzzZwmvK3FoC2vO4PDIuvW5BImuuc8_43-ux924xmugBQb8muaDCc4eu8GVM9uusH2nq-udLuHquudPYVIOuLPmDXmvKSqR9uvfS3C9OuX" +
      "UnEXOvQU-Gw-u3VPT8uvYVUSnWvwWeDZ2uRZ6ea-vNeeiUGuyfFyMGvBibS62uToNyT2vIpJZX2vspRoKeukpiHL2uUyVzXmvI0S7-OvI0aYeuua" +
      "2KrG-u53zpOGvR56ubWvOA8LX-uuA9VbOvLEk-RuuXHVZG2ulN2pbWvkPGaTWuSSxqJuvIUvbVevoU4GeGvZX8zzWumcmsG2uqeGoLevlf02eeuY" +
      "gWRTWvahFaUeudwEZ62vIzr6VeuT196jOui4SVIGvQ43NxGuX52WwGu5_bziWuQ_nmUeuSBWl4uwfCOnDewyGa8cexKLacw-wcNGpA-wfOwBN2xS" +
      "R3XL2xmTvbnWxWXHDSOwSjBXC-xSqE9kGwb1VLSuwQ8YtpuwcBkXrmw1GVl4mw3K9qc-wSNqyXWxsPx9UuwaQqZs-wvRNoBuxURuri-wWR-lPWwT" +
      "SwXfextS2UPOwjTYNTOxOWSEwewQXIEa-wYXEhvuwaX4ZXOwgX-64exIaEdE-xqe7-KWxMnziqGxToS2jmxoqQZWGw3rqbAWxpsCShexWuIl12xQ" +
      "yHHfmxi2vOqWwd8NWKOwv-V2qewjDA0UGwhHJDJuwtQMHZ2wWRMdMWxmR4pkWwcVw0FGwQXjVFmxEb-nwewWgGL02wmg6mBuwUkInGOxJnbDWGxK" +
      "xNoBGwy4T7cexU8YtDGxoCQTd-yrFlOw-zIHhpjWyWLUY4-yUP84DOyaRE2-ezXRTy8mzQSHsVmzRT5p5-ysXz6e2zLed0y2zKfMFHOzjiB4ruyq" +
      "jHJjuywjHJjuy3jYGOmzMjao1my2rSG8uzgs9UVeydyia7Oy2zEYimyq1bKN2yr3FGq-yT-ubfOzMBV6pOylDm6jezeFbYPuy3H8XwOyZJGdvez_" +
      "JnWcuySK-qk-yqMVnx-ynOTbt2ySRapBuygUxz2-ySVxDvWyPXMz9uykYFDXOyTankz2yocvCSeyWcwS9OyVd5iS-yWmNyjeyoqPIMezMr5nU2zv" +
      "ufTf-zOu49f-y3yoJNey0y_64-yq39YYeywB_WC2yqDR4rGypEjpzWzDIzycey3KHl4OydLpCXezJRcEpmzLVT0geysYWI8uyUYvnb2zUbc3SGyo" +
      "ctaumyWdC2Neywid90Oynl3-K-zondVrmzIpTz2OzwprrlmzFp5UrGzKsyod2yYwI3ReysyH0aOzAyNWMezg2Frlmzs4smKmzU5T8IuzK53l7uzI" +
      "7MdDWyy9ft-WzY_TGYGyVAhU4O0vAimZ-1jEilIG1OGvIM-1YJ-n5e0UOYWw20PSFL3-01Tfkg-0aT6one0kUGIK-0kUKZaG0cYpEKG0SZtLk-0k" +
      "dAC6e0he7jxG0mi7LLu0VjLEJW1Oj223u1lk-zTm0UltMZW1soR82W1Jro-JG1RsBp0e1atGHc-1PtaK--0auXjx-0UvBzJ-0jxFUFG0QxBJle1Y" +
      "yOK5O0d2jGYe0W8g7k20SFUdvm0aHgyau0eIMXU20jKPKRm0kLlZV20kMMHM-1iO63ke0lSG0oO0VW5i020SYzjdm0WalpG20XcDPVm0sfJZ5e1K" +
      "gCmQO0Popal-0apn44-1I1NCw-0Y4lEfu0v8yGQe1IEAcLe1LF554u0uIS3dW1pLltym1CMoysO0jPeIku0kQ4HTm0QRUziO0tRkafe0YRrlIG1U" +
      "SS5720YUoMe-0ZXBFqu0XYtNC21nYozD-1Kaesbe0dfa88e1YlsL5e1orkxAm1gr6STu0rw2qLG1myCele1HyqKVO1X0j5DW011Ztwu1n65NlO1g" +
      "7Qfp20YAcgsW1OEYefe1JF6FRO0YGC6920YGT4CW1sGvg-G1KICsp20WI8p4W0WKhMgW0tKvH3O0SLzJ-W0mL1Ky21KOYNHW0YTgVo21JWcl3O1j" +
      "bDiJu1KbQzcm0miMPae0YybwNu1ZwG52m0UxglEO0Uy_rNW0UzdZB-0j1K5A-0Y2MmTO1f4s2pu1r_OGoO1eDJOHO2YGlqo223JCMX-2WLRYr-2r" +
      "Mk72u2ZPNk622WPdJPG2QPxTUm2oRoLau3_SFWt-2XVQoMu3HWUBee2aXb31O2bYxhV-2ab8yS-32fXj8G2Tg4cWu3shSaTe2Wl_o5e3LsW8-u3P" +
      "teTRO2xuhz7O2W5bUV23Q6Qwpe2-6DKCm3g6O5iW2s619nG3o7wxk-25_YWV22nGMcNm2YG-7C-3mHJKZ-2eMzdC22mNrp0O2eOOW5-2TQr5b22S" +
      "Se19m2QTx5Ce2eUuY9W2aVrp6224ehCkW2VfOd7u3ZfxFtu3FnwFz23b1VE6u2i4IkkW2t4YWHe2a54YgW3r64X622k_E8fG2W_rI-W2i",
    c: [["Ori","Orion","AJAZAJA1AZBDBDAcAcA1A1A4BDAGAZErAJErAGA4"],
      ["UMa","Ursa Major","AiBQBQBWBWDsDsAiDsAfAfBKBKAm"],
      ["UMi","Ursa Minor","AyMBMBKKKKLYLYX4X4C6C6A6A6LY"],
      ["Cas","Cassiopeia","D9BtBtBaBaBCBCBJ"],
      ["Cyg","Cygnus","ASBABAHSHSC9CSBABABZBZDV"],
      ["Lyr","Lyra","AEbQAEMDMDLMLMDeDeESESMD"],
      ["Aql","Aquila","B3ALALFtALD6D6HUHUDZD6EPD6Cp"],
      ["Sco","Scorpius","BoBPBPCYBPCZCZANANCICIBLBLC8C8FNFNDwDwAnAnC1C1BTBTAY"],
      ["Sgr","Sagittarius","CoB2CoAkB2AkB2CHCHDQDQB2DQBkBkAkDQAzAzDvDvBk"],
      ["Leo","Leo","AVEjEjBlBlEOEOHJHJCmBlBfBfA-A-DyDyAVBfDy"],
      ["Gem","Gemini","AuAPAuMoMoClClCUCUDnAPEmEmGPGPAq"],
      ["Tau","Taurus","FVGBGBElElAaFVEBEBAMAMCrFVEU"],
      ["CMa","Canis Major","AAAtAAAjAjAWAjBY"],
      ["CMi","Canis Minor","AHCb"],
      ["Cru","Crux","ATAXARCE"],
      ["Cen","Centaurus","ADAKAKBMBMA_BMBe"],
      ["Boo","Bootes","ACB1B1EXEXEeEeC0C0E9E9ACACM9ACBu"],
      ["CrB","Corona Borealis","JaFhFhBEBEGtGtQOQOJh"],
      ["Her","Hercules","HdCGCGEoEoDLDLHdCGB-HdDK"],
      ["Per","Perseus","AhCuCuCWCWCMAhCeCeGAAhA9"],
      ["Aur","Auriga","AFAoAoBnBnAaAaBwBwAF"],
      ["And","Andromeda","A2DhDhA3A3BIA3G9G9Og"],
      ["Peg","Pegasus","BbBUBUA2A2CJCJBbBbEDEDEpEpBSBUCgBUEbEbHs"],
      ["Cep","Cepheus","BXDaDaDXDXEkEkD2D2BX"],
      ["Dra","Draco","CCBFBFF-F-VsVsCCF-C7C7DPDPB5B5IJIJDpDpFXFXHEHEGs"],
      ["Vir","Virgo","FJHPHPFWFWAOFWD_D_CKAOD7D7D_"],
      ["Lib","Libra","B7BmBmHbB7Do"],
      ["Cap","Capricornus","E7C-C-JbJbJKJKF4F4CTCTFiFiK4K4I0I0E7"],
      ["Aqr","Aquarius","GLCdCdCkCkGvGvM5M5IXCkJnJnF5F5Dm"],
      ["Psc","Pisces","FKKcKcLcLcKvKvM6M6IPIPJWJWK6K6FmFmXoXoOGOGJW"],
      ["Ari","Aries","AwBpBpSe"],
      ["Cnc","Cancer","EhHjHjQzQzIRHjKZ"],
      ["Oph","Ophiuchus","A7DUDUB4B4DdDdBgBgBVBVB_B_A7"],
      ["Crv","Corvus","BiCiCiBrBrCsCsBi"],
      ["Del","Delphinus","FTGKGKKtKtNANAFTFTIc"],
      ["Lep","Lepus","BhCLBhDrDrDSCLDSBhEvCLFDFDGaGaEv"]] };
})();
