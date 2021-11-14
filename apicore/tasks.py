from celery import shared_task
import requests
from apicore.models import *
from types import SimpleNamespace
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from django.utils import timezone
import datetime

item_search_details = [
    [6, 'ability_mount_ridinghorse'],
    [7, 'ability_mount_whitedirewolf'],
    [8, 'ability_mount_ridinghorse'],
    [9, 'ability_mount_ridinghorse'],
    [11, 'ability_mount_ridinghorse'],
    [12, 'ability_mount_blackdirewolf'],
    [13, 'ability_mount_blackdirewolf'],
    [14, 'ability_mount_blackdirewolf'],
    [15, 'ability_mount_whitedirewolf'],
    [17, 'spell_nature_swiftness'],
    [18, 'ability_mount_ridinghorse'],
    [19, 'ability_mount_whitedirewolf'],
    [20, 'ability_mount_blackdirewolf'],
    [21, 'ability_mount_mountainram'],
    [22, 'ability_mount_mountainram'],
    [24, 'ability_mount_mountainram'],
    [25, 'ability_mount_mountainram'],
    [26, 'ability_mount_whitetiger'],
    [27, 'ability_mount_raptor'],
    [28, 'ability_mount_undeadhorse'],
    [31, 'ability_mount_whitetiger'],
    [32, 'ability_mount_jungletiger'],
    [34, 'ability_mount_blackpanther'],
    [35, 'ability_mount_raptor'],
    [36, 'ability_mount_raptor'],
    [38, 'ability_mount_raptor'],
    [39, 'ability_mount_mechastrider'],
    [40, 'ability_mount_mechastrider'],
    [41, 'spell_nature_swiftness'],
    [42, 'ability_mount_mechastrider'],
    [43, 'ability_mount_mechastrider'],
    [45, 'ability_mount_blackpanther'],
    [46, 'ability_mount_whitetiger'],
    [50, 'ability_mount_blackdirewolf'],
    [51, 'ability_mount_whitedirewolf'],
    [52, 'ability_mount_ridinghorse'],
    [53, 'ability_mount_ridinghorse'],
    [54, 'ability_mount_raptor'],
    [55, 'ability_mount_pinktiger'],
    [56, 'ability_mount_raptor'],
    [57, 'ability_mount_mechastrider'],
    [58, 'ability_mount_mechastrider'],
    [62, 'ability_mount_mechastrider'],
    [63, 'ability_mount_mountainram'],
    [64, 'ability_mount_mountainram'],
    [65, 'ability_mount_undeadhorse'],
    [66, 'ability_mount_undeadhorse'],
    [67, 'ability_mount_undeadhorse'],
    [68, 'ability_mount_undeadhorse'],
    [69, 'ability_mount_undeadhorse'],
    [70, 'inv_misc_head_tauren_02'],
    [71, 'ability_mount_kodo_01'],
    [72, 'ability_mount_kodo_03'],
    [73, 'ability_mount_kodo_02'],
    [74, 'ability_mount_kodo_02'],
    [75, 'ability_mount_nightmarehorse'],
    [76, 'ability_mount_kodo_01'],
    [77, 'ability_mount_blackbattlestrider'],
    [78, 'ability_mount_mountainram'],
    [79, 'ability_mount_raptor'],
    [80, 'ability_mount_undeadhorse'],
    [81, 'ability_mount_blackpanther'],
    [82, 'ability_mount_blackdirewolf'],
    [83, 'ability_mount_dreadsteed'],
    [84, 'ability_mount_charger'],
    [85, 'ability_mount_blackpanther'],
    [87, 'ability_mount_whitetiger'],
    [88, 'ability_mount_mechastrider'],
    [89, 'ability_mount_mechastrider'],
    [90, 'ability_mount_mechastrider'],
    [91, 'ability_mount_ridinghorse'],
    [92, 'ability_mount_ridinghorse'],
    [93, 'ability_mount_ridinghorse'],
    [94, 'ability_mount_mountainram'],
    [95, 'ability_mount_mountainram'],
    [96, 'ability_mount_mountainram'],
    [97, 'ability_mount_raptor'],
    [98, 'ability_mount_raptor'],
    [99, 'ability_mount_raptor'],
    [100, 'ability_mount_undeadhorse'],
    [101, 'ability_mount_kodo_01'],
    [102, 'ability_mount_kodo_01'],
    [103, 'ability_mount_kodo_03'],
    [104, 'ability_mount_blackdirewolf'],
    [105, 'ability_mount_whitedirewolf'],
    [106, 'ability_mount_whitedirewolf'],
    [107, 'ability_mount_blackpanther'],
    [108, 'ability_mount_whitedirewolf'],
    [109, 'ability_mount_mountainram'],
    [110, 'ability_mount_raptor'],
    [111, 'ability_mount_jungletiger'],
    [116, 'inv_misc_qirajicrystal_05'],
    [117, 'inv_misc_qirajicrystal_04'],
    [118, 'inv_misc_qirajicrystal_02'],
    [119, 'inv_misc_qirajicrystal_01'],
    [120, 'inv_misc_qirajicrystal_03'],
    [121, 'inv_misc_qirajicrystal_05'],
    [122, 'inv_misc_qirajicrystal_05'],
    [123, 'ability_mount_netherdrakepurple'],
    [125, 'ability_hunter_pet_turtle'],
    [129, 'ability_mount_goldengryphon'],
    [130, 'ability_mount_ebongryphon'],
    [131, 'ability_mount_snowygryphon'],
    [132, 'ability_mount_gryphon_01'],
    [133, 'ability_mount_tawnywindrider'],
    [134, 'ability_mount_bluewindrider'],
    [135, 'ability_mount_greenwindrider'],
    [136, 'ability_mount_swiftredwindrider'],
    [137, 'ability_mount_gryphon_01'],
    [138, 'ability_mount_gryphon_01'],
    [139, 'ability_mount_gryphon_01'],
    [140, 'ability_mount_swiftgreenwindrider'],
    [141, 'ability_mount_swiftyellowwindrider'],
    [142, 'ability_mount_swiftpurplewindrider'],
    [145, 'ability_mount_mechastrider'],
    [146, 'ability_mount_cockatricemountelite'],
    [147, 'ability_mount_ridingelekk'],
    [149, 'ability_mount_charger'],
    [150, 'spell_nature_swiftness'],
    [151, 'inv_misc_foot_centaur'],
    [152, 'ability_mount_cockatricemount'],
    [153, 'inv_misc_foot_centaur'],
    [154, 'inv_misc_foot_centaur'],
    [155, 'inv_misc_foot_centaur'],
    [156, 'inv_misc_foot_centaur'],
    [157, 'ability_mount_cockatricemount_purple'],
    [158, 'ability_mount_cockatricemount_blue'],
    [159, 'ability_mount_cockatricemount_black'],
    [160, 'ability_mount_cockatricemountelite_green'],
    [161, 'ability_mount_cockatricemountelite_purple'],
    [162, 'ability_mount_cockatricemountelite_black'],
    [163, 'ability_mount_ridingelekk_grey'],
    [164, 'ability_mount_ridingelekk_purple'],
    [165, 'ability_mount_ridingelekkelite_green'],
    [166, 'ability_mount_ridingelekkelite_blue'],
    [167, 'ability_mount_ridingelekkelite_purple'],
    [168, 'ability_mount_dreadsteed'],
    [169, 'ability_mount_netherdrakeelite'],
    [170, 'inv_misc_foot_centaur'],
    [171, 'inv_misc_foot_centaur'],
    [172, 'inv_misc_foot_centaur'],
    [173, 'inv_misc_foot_centaur'],
    [174, 'inv_misc_foot_centaur'],
    [176, 'ability_hunter_pet_netherray'],
    [177, 'ability_hunter_pet_netherray'],
    [178, 'ability_hunter_pet_netherray'],
    [179, 'ability_hunter_pet_netherray'],
    [180, 'ability_hunter_pet_netherray'],
    [183, 'inv_misc_summerfest_brazierorange'],
    [185, 'inv-mount_raven_54'],
    [186, 'ability_mount_netherdrakepurple'],
    [187, 'ability_mount_netherdrakepurple'],
    [188, 'ability_mount_netherdrakepurple'],
    [189, 'ability_mount_netherdrakepurple'],
    [190, 'ability_mount_netherdrakepurple'],
    [191, 'ability_mount_netherdrakepurple'],
    [196, 'ability_mount_spectraltiger'],
    [197, 'ability_mount_spectraltiger'],
    [199, 'ability_druid_challangingroar'],
    [201, 'ability_mount_mountainram'],
    [202, 'ability_mount_mountainram'],
    [203, 'ability_mount_warhippogryph'],
    [204, 'ability_mount_gyrocoptorelite'],
    [205, 'ability_mount_gyrocoptor'],
    [206, 'ability_mount_netherdrakeelite'],
    [207, 'ability_mount_netherdrakeelite'],
    [211, 'inv_misc_missilesmall_blue'],
    [212, 'inv_misc_missilesmall_red'],
    [213, 'ability_mount_cockatricemountelite_white'],
    [219, 'ability_mount_nightmarehorse'],
    [220, 'ability_mount_ridingelekkelite_blue'],
    [221, 'spell_deathknight_summondeathcharger'],
    [222, 'ability_mount_charger'],
    [223, 'ability_mount_netherdrakeelite'],
    [224, 'ability_mount_charger'],
    [225, 'ability_mount_kotobrewfest'],
    [226, 'ability_mount_kotobrewfest'],
    [230, 'ability_druid_challangingroar'],
    [236, 'ability_mount_ebonblade'],
    [237, 'ability_mount_polarbear_white'],
    [238, 'ability_mount_gryphon_01'],
    [240, 'inv_misc_key_14'],
    [241, 'ability_mount_netherdrakeelite'],
    [243, 'ability_mount_bigblizzardbear'],
    [246, 'ability_mount_drake_azure'],
    [247, 'ability_mount_drake_azure'],
    [248, 'ability_mount_drake_bronze'],
    [249, 'ability_mount_drake_red'],
    [250, 'ability_mount_drake_twilight'],
    [251, 'ability_mount_polarbear_black'],
    [253, 'ability_mount_drake_twilight'],
    [254, 'ability_mount_mammoth_black'],
    [255, 'ability_mount_mammoth_black'],
    [256, 'ability_mount_mammoth_brown'],
    [257, 'ability_mount_mammoth_brown'],
    [258, 'ability_mount_mammoth_white'],
    [259, 'ability_mount_mammoth_white'],
    [262, 'ability_mount_drake_proto'],
    [263, 'ability_mount_drake_proto'],
    [264, 'ability_mount_drake_proto'],
    [265, 'ability_mount_drake_proto'],
    [266, 'ability_mount_drake_proto'],
    [267, 'ability_mount_drake_proto'],
    [268, 'ability_mount_drake_blue'],
    [269, 'ability_mount_polarbear_brown'],
    [270, 'ability_mount_polarbear_brown'],
    [271, 'ability_mount_polarbear_black'],
    [272, 'ability_mount_polarbear_black'],
    [273, 'ability_mount_mammoth_brown'],
    [274, 'ability_mount_mammoth_brown'],
    [275, 'inv_misc_key_14'],
    [276, 'ability_mount_gryphon_01'],
    [277, 'ability_mount_swiftpurplewindrider'],
    [278, 'ability_mount_drake_proto'],
    [279, 'ability_mount_magnificentflyingcarpet'],
    [280, 'ability_mount_mammoth_brown_3seater'],
    [284, 'ability_mount_mammoth_brown_3seater'],
    [285, 'ability_mount_flyingcarpet'],
    [286, 'ability_mount_mammoth_black_3seater'],
    [287, 'ability_mount_mammoth_black_3seater'],
    [288, 'ability_mount_mammoth_white_3seater'],
    [289, 'ability_mount_mammoth_white_3seater'],
    [291, 'ability_hunter_pet_dragonhawk'],
    [292, 'ability_hunter_pet_dragonhawk'],
    [293, 'ability_hunter_pet_dragonhawk'],
    [294, 'ability_mount_ridinghorse'],
    [295, 'ability_mount_raptor'],
    [296, 'ability_mount_mountainram'],
    [297, 'ability_mount_whitetiger'],
    [298, 'ability_mount_mechastrider'],
    [299, 'ability_mount_ridingelekkelite'],
    [300, 'ability_mount_blackdirewolf'],
    [301, 'ability_mount_kodo_01'],
    [302, 'ability_mount_cockatricemountelite_purple'],
    [303, 'ability_mount_undeadhorse'],
    [304, 'inv_misc_enggizmos_03'],
    [305, 'ability_mount_warhippogryph'],
    [306, 'ability_mount_razorscale'],
    [307, 'ability_mount_razorscale'],
    [308, 'ability_mount_undeadhorse'],
    [309, 'ability_mount_kodo_01'],
    [310, 'ability_mount_blackdirewolf'],
    [311, 'ability_mount_raptor'],
    [312, 'inv_misc_fish_turtle_02'],
    [313, 'ability_mount_redfrostwyrm_01'],
    [314, 'ability_mount_undeadhorse'],
    [317, 'ability_mount_redfrostwyrm_01'],
    [318, 'ability_mount_ridingelekkelite'],
    [319, 'ability_mount_whitetiger'],
    [320, 'ability_mount_cockatricemountelite_purple'],
    [321, 'ability_mount_ridinghorse'],
    [322, 'ability_mount_kodo_01'],
    [323, 'ability_mount_mechastrider'],
    [324, 'ability_mount_mountainram'],
    [325, 'ability_mount_raptor'],
    [326, 'ability_mount_undeadhorse'],
    [327, 'ability_mount_blackdirewolf'],
    [328, 'inv_egg_03'],
    [329, 'ability_mount_warhippogryph'],
    [330, 'ability_hunter_pet_dragonhawk'],
    [331, 'ability_mount_ridinghorse'],
    [332, 'ability_mount_cockatricemountelite_purple'],
    [333, 'spell_magic_polymorphchicken'],
    [334, 'spell_magic_polymorphchicken'],
    [335, 'spell_magic_polymorphchicken'],
    [336, 'ability_mount_undeadhorse'],
    [337, 'ability_mount_whitetiger'],
    [338, 'ability_mount_charger'],
    [340, 'ability_mount_redfrostwyrm_01'],
    [341, 'ability_mount_ridinghorse'],
    [342, 'ability_mount_blackdirewolf'],
    [343, 'ability_mount_ridinghorse'],
    [344, 'ability_mount_ridinghorse'],
    [345, 'ability_mount_nightmarehorse'],
    [349, 'achievement_boss_onyxia'],
    [350, 'ability_mount_kodo_03'],
    [351, 'ability_mount_kodosunwalkerelite'],
    [352, 'inv_valentinepinkrocket'],
    [358, 'ability_mount_redfrostwyrm_01'],
    [363, 'ability_mount_pegasus'],
    [364, 'ability_mount_redfrostwyrm_01'],
    [365, 'ability_mount_redfrostwyrm_01'],
    [366, 'spell_deathknight_summondeathcharger'],
    [367, 'spell_nature_swiftness'],
    [368, 'ability_mount_charger'],
    [371, 'ability_mount_warhippogryph'],
    [372, 'ability_hunter_pet_rhino'],
    [373, 'ability_mount_seahorse'],
    [375, 'ability_mount_frostyflyingcarpet'],
    [376, 'ability_mount_celestialhorse'],
    [382, 'ability_mount_rocketmount2'],
    [386, 'ability_mount_fossilizedraptor'],
    [388, 'inv_misc_key_03'],
    [389, 'inv_misc_key_04'],
    [391, 'inv_misc_stonedragonred'],
    [392, 'inv_misc_stormdragonred'],
    [393, 'inv_misc_stonedragonpurple'],
    [394, 'inv_misc_stormdragongreen'],
    [395, 'inv_misc_stormdragonpale'],
    [396, 'inv_misc_stormdragonpurple'],
    [397, 'inv_misc_stonedragonblue'],
    [398, 'ability_mount_camel_brown'],
    [399, 'ability_mount_camel_tan'],
    [400, 'ability_mount_camel_gray'],
    [401, 'inv_mount_darkphoenixa'],
    [403, 'inv_mount_allianceliong'],
    [404, 'trade_archaeology_sceptor of azaqir'],
    [405, 'inv_mount_spectralhorse'],
    [406, 'inv_mount_spectralwolf'],
    [407, 'inv_misc_stonedragonorange'],
    [408, 'ability_mount_drake_bronze'],
    [409, 'inv_mount_hordescorpiong'],
    [410, 'ability_mount_raptor'],
    [411, 'ability_mount_blackpanther'],
    [412, 'ability_hunter_pet_dragonhawk'],
    [413, 'ability_mount_warhippogryph'],
    [415, 'inv_misc_orb_05'],
    [416, 'inv_misc_summerfest_braziergreen'],
    [417, 'inv_misc_orb_04'],
    [418, 'ability_mount_raptor'],
    [419, 'ability_druid_challangingroar'],
    [420, 'ability_mount_seahorse'],
    [421, 'inv_mount_wingedlion'],
    [422, 'ability_mount_alliancepvpmount'],
    [423, 'ability_mount_hordepvpmount'],
    [424, 'ability_mount_drake_twilight'],
    [425, 'ability_mount_fireravengodmount'],
    [426, 'ability_hunter_pet_tallstrider'],
    [428, 'ability_mount_drake_twilight'],
    [429, 'ability_hunter_pet_tallstrider'],
    [430, 'ability_hunter_pet_tallstrider'],
    [431, 'ability_hunter_pet_tallstrider'],
    [432, 'ability_mount_camel_gray'],
    [433, 'ability_mount_warhippogryph'],
    [434, 'ability_hunter_pet_bear'],
    [435, 'ability_mount_ridinghorse'],
    [436, 'ability_mount_ridinghorse'],
    [439, 'ability_mount_tyraelmount'],
    [440, 'ability_mount_spectralgryphon'],
    [441, 'ability_mount_spectralwyvern'],
    [442, 'ability_mount_drake_red'],
    [443, 'ability_mount_drake_red'],
    [444, 'ability_mount_drake_red'],
    [445, 'ability_mount_drake_twilight'],
    [446, 'inv_dragonchromaticmount'],
    [447, 'ability_mount_feldrake'],
    [448, 'inv_pandarenserpentmount_green'],
    [449, 'ability_mount_waterstridermount'],
    [450, 'ability_mount_pandarenkitemount'],
    [451, 'ability_mount_onyxpanther'],
    [452, 'ability_mount_pandaranmountgreen'],
    [453, 'ability_mount_pandaranmountepicred'],
    [454, 'inv_lavahorse'],
    [455, 'inv_misc_reforgedarchstone_01'],
    [456, 'ability_mount_onyxpanther_blue'],
    [457, 'ability_mount_onyxpanther_green'],
    [458, 'ability_mount_onyxpanther_red'],
    [459, 'ability_mount_onyxpanther_yellow'],
    [460, 'ability_mount_travellersyakmount'],
    [462, 'ability_mount_yakmount'],
    [463, 'ability_mount_hordescorpionamber'],
    [464, 'inv_pandarenserpentmount_blue'],
    [465, 'inv_pandarenserpentmount_yellow'],
    [466, 'inv_pandarenserpentmount_lightning_green'],
    [467, 'ability_mount_drake_twilight'],
    [468, 'ability_mount_quilenflyingmount'],
    [469, 'ability_mount_rocketmount3'],
    [470, 'ability_mount_rocketmount4'],
    [471, 'inv_pandarenserpentmount_blue'],
    [472, 'inv_jewelcrafting_rubyserpent'],
    [473, 'inv_pandarenserpentgodmount_black'],
    [474, 'inv_pandarenserpentgodmount_red'],
    [475, 'inv_pandarenserpentgodmount_gold'],
    [476, 'ability_monk_summonserpentstatue'],
    [477, 'inv_bluegodcloudserpent'],
    [478, 'inv_celestialserpentmount'],
    [479, 'ability_mount_cranemountblue'],
    [480, 'ability_mount_cranemount'],
    [481, 'ability_mount_cranemountpurple'],
    [484, 'ability_mount_yakmountblack'],
    [485, 'ability_mount_yakmountwhite'],
    [486, 'ability_mount_yakmountgrey'],
    [487, 'ability_mount_yakmountbrown'],
    [488, 'ability_mount_waterstridermount'],
    [492, 'ability_mount_pandaranmountblack'],
    [493, 'ability_mount_pandaranmountblue'],
    [494, 'ability_mount_pandaranmountbrown'],
    [495, 'ability_mount_pandaranmountpurple'],
    [496, 'ability_mount_pandaranmountred'],
    [497, 'ability_mount_pandaranmountepic'],
    [498, 'ability_mount_pandaranmountepicblack'],
    [499, 'ability_mount_pandaranmountepicblue'],
    [500, 'ability_mount_pandaranmountepicbrown'],
    [501, 'ability_mount_pandaranmountepicpurple'],
    [503, 'ability_mount_pandarenphoenix_red'],
    [504, 'inv_pandarenserpentmount_lightning_yellow'],
    [505, 'ability_mount_siberiantigermount'],
    [506, 'ability_mount_siberiantigermount'],
    [507, 'ability_mount_siberiantigermount'],
    [508, 'ability_mount_goatmountbrown'],
    [509, 'ability_mount_cloudmount'],
    [510, 'ability_mount_goatmountwhite'],
    [511, 'ability_mount_goatmountblack'],
    [515, 'inv_mushanbeastmount'],
    [516, 'ability_mount_pandarenkitemount_blue'],
    [517, 'inv_pandarenserpentmount_lightning'],
    [518, 'ability_mount_pandarenphoenix_green'],
    [519, 'ability_mount_pandarenphoenix_yellow'],
    [520, 'ability_mount_pandarenphoenix_purple'],
    [521, 'ability_mount_pandarenkitemount_blue'],
    [522, 'ability_mount_shreddermount'],
    [523, 'ability_mount_swiftwindsteed'],
    [526, 'inv_misc_elitegryphonarmored'],
    [527, 'inv_misc_elitewyvernarmored'],
    [528, 'inv_misc_elitegryphon'],
    [529, 'inv_misc_elitewyvern'],
    [530, 'ability_mount_pterodactylmount'],
    [531, 'ability_mount_triceratopsmount'],
    [532, 'inv_ghostlycharger'],
    [533, 'ability_mount_triceratopsmount_blue'],
    [534, 'ability_mount_triceratopsmount_yellow'],
    [535, 'ability_mount_triceratopsmount_grey'],
    [536, 'ability_mount_triceratopsmount_green'],
    [537, 'ability_mount_raptor_white'],
    [538, 'ability_hunter_pet_raptor'],
    [539, 'ability_mount_raptor_black'],
    [540, 'ability_mount_raptor'],
    [541, 'inv_pandarenserpentmount_white'],
    [542, 'inv_pandarenserpentmount_lightning_blue'],
    [543, 'achievement_boss_ji-kun'],
    [544, 'ability_mount_epicbatmount'],
    [545, 'ability_mount_triceratopsmount_orange'],
    [546, 'ability_mount_triceratopsmount_red'],
    [547, 'inv_pegasusmount'],
    [548, 'ability_mount_dragonhawkarmorhorde'],
    [549, 'ability_mount_dragonhawkarmorallliance'],
    [550, 'inv_mushanbeastmount'],
    [551, 'inv_faeriedragonmount'],
    [552, 'ability_mount_steelwarhorse'],
    [554, 'ability_mount_warnightsaber'],
    [555, 'inv_skeletalwarhorse'],
    [557, 'ability_mount_korkronprotodrake'],
    [558, 'ability_mount_hordepvpmount'],
    [559, 'inv_mount_hordescorpiong'],
    [560, 'inv_mushanbeastmountblack'],
    [561, 'inv_pandarenserpentmount_lightning_black'],
    [562, 'inv_pandarenserpentmount_white'],
    [563, 'inv_pandarenserpentmount_white'],
    [564, 'inv_pandarenserpentmount_white'],
    [568, 'inv_misc_elitehippogryph'],
    [571, 'ability_mount_ironchimera'],
    [593, 'ability_mount_clockworkhorse'],
    [594, 'ability_mount_ravager2mount'],
    [600, 'inv_ravenlordmount'],
    [603, 'inv_tailoring_blackcarpet'],
    [606, 'ability_hunter_pet_corehound'],
    [607, 'inv_lessergronnmount_red'],
    [608, 'inv_clefthoofdraenormount_blue'],
    [609, 'inv_clefthoofdraenormount_blue'],
    [611, 'inv_clefthoofdraenormount_blue'],
    [612, 'inv_clefthoofdraenormount_blue'],
    [613, 'inv_ironhordeclefthoof'],
    [614, 'ability_mount_elekkdraenormount'],
    [615, 'ability_mount_elekkdraenormount'],
    [616, 'ability_mount_elekkdraenormount'],
    [617, 'ability_mount_elekkdraenormount'],
    [618, 'inv_iron horde elekk'],
    [619, 'inv_giantboarmount_brown'],
    [620, 'inv_giantboarmount_brown'],
    [621, 'inv_giantboarmount_brown'],
    [622, 'inv_giantboarmount_brown'],
    [623, 'inv_giantboarmount_brown'],
    [624, 'inv_giantboarmount_brown'],
    [625, 'inv_giantboarmount_brown'],
    [626, 'inv_giantboarmount_brown'],
    [627, 'inv_giantboarmount_brown'],
    [628, 'inv_giantboarmount_brown'],
    [629, 'inv_hippo_green'],
    [630, 'inv_hippo_green'],
    [631, 'inv_hippo_green'],
    [632, 'inv_hippo_green'],
    [633, 'inv_infernalmountred'],
    [634, 'inv_helm_suncrown_d_01'],
    [635, 'ability_mount_talbukdraenormount'],
    [636, 'ability_mount_talbukdraenormount'],
    [637, 'ability_mount_talbukdraenormount'],
    [638, 'ability_mount_talbukdraenormount'],
    [639, 'inv_talbukdraenor_white'],
    [640, 'ability_mount_mountainram'],
    [641, 'ability_mount_viciouswarraptor'],
    [642, 'inv_wolfdraenormountshadow'],
    [643, 'inv_wolfdraenormountbrown'],
    [644, 'inv_wolfdraenormountfrost'],
    [645, 'inv_wolfdraenormountred'],
    [647, 'inv_wolfdraenormountbrown'],
    [648, 'inv_wolfdraenormountfrost'],
    [649, 'inv_wolfdraenormountred'],
    [650, 'inv_wolfdraenormountbrown'],
    [651, 'inv_chopper_horde'],
    [652, 'inv_chopper_alliance'],
    [654, 'inv_misc_pet_pandaren_yeti'],
    [655, 'inv_lessergronnmount_red'],
    [656, 'foxmounticon'],
    [657, 'ability_mount_blackdirewolf'],
    [663, 'inv_spidermount'],
    [664, 'ability_mount_drake_blue'],
    [678, 'inv_misc_key_06'],
    [679, 'inv_misc_key_06'],
    [682, 'ability_mount_fireravengodmountpurple'],
    [741, 'inv_saber2mount'],
    [751, 'ability_mount_felreavermount'],
    [753, 'inv_feldreadravenmount'],
    [755, 'ability_mount_viciouswarmechanostrider'],
    [756, 'ability_mount_viciouswarkodo'],
    [758, 'inv_wolfdraenor_felmount'],
    [759, 'inv_fellessergronnmount'],
    [760, 'inv_fellessergronnmount_pale'],
    [761, 'inv_fellessergronnmount_dark'],
    [762, 'inv_lessergronnmount_red'],
    [763, 'inv_felstalkermount'],
    [764, 'inv_moosemount'],
    [765, 'inv_giantboarmount_brown'],
    [768, 'inv_giantboarmount_brown'],
    [769, 'inv_misc_pet_pandaren_yeti_grey'],
    [772, 'spell_beastmaster_rylak'],
    [773, 'inv_moosemount2nightmare'],
    [775, 'inv_alliancepvpmount'],
    [776, 'spell_beastmaster_rylak'],
    [778, 'ability_hunter_pet_dragonhawk'],
    [779, 'inv_ghostlymoosemount'],
    [780, 'inv_dhmount_felsaber'],
    [781, 'inv_infinitedragonmount'],
    [784, 'ability_mount_hordepvpmount'],
    [791, 'inv_infernalmount'],
    [793, 'inv_falcosaurosblack'],
    [794, 'inv_falcosaurosred'],
    [795, 'inv_falcosauroswhite'],
    [796, 'inv_falcosaurosgreen'],
    [797, 'inv_mount_felcorehoundmoun'],
    [800, 'inv_fishmount'],
    [802, 'ability_mount_warhippogryph'],
    [804, 'inv_ratmount'],
    [826, 'inv_horse2mount'],
    [831, 'inv_horse2mountpurple'],
    [832, 'inv_horse2mountgreen'],
    [833, 'inv_horse2mountlight'],
    [834, 'inv_horse2mountyellow'],
    [836, 'inv_horse2mountblack'],
    [838, 'inv_fishing_lure_starfish'],
    [841, 'inv_mount_vicioushorse'],
    [842, 'inv_viciousgoblintrike'],
    [843, 'ability_mount_vicioushawkstrider'],
    [844, 'ability_mount_viciouswarelekk'],
    [845, 'ability_mount_shreddermount'],
    [846, 'inv_mount_hippogryph_arcane'],
    [847, 'inv_turtlemount'],
    [848, 'inv_stormdragonmount2'],
    [849, 'inv_stormdragonmount2blue'],
    [850, 'inv_stormdragonmount2dark'],
    [851, 'inv_stormdragonmount2green'],
    [852, 'inv_stormdragonmount2light'],
    [853, 'inv_stormdragonmount2yellow'],
    [854, 'inv_moosemount2white'],
    [855, 'inv_stingray2mount'],
    [860, 'inv_magemount'],
    [861, 'inv_priestmount'],
    [864, 'inv_monkmount'],
    [865, 'inv_huntermount'],
    [866, 'ability_mount_dkmount'],
    [867, 'inv_warriormount'],
    [868, 'inv_dhmount'],
    [870, 'inv_huntermount_green'],
    [872, 'inv_huntermount_blue'],
    [873, 'inv_mount_viciousalliancebearmount'],
    [874, 'inv_mount_vicioushordebearmount'],
    [875, 'ability_mount_dreadsteed'],
    [876, 'inv_viciousgoldenking'],
    [877, 'inv_ability_mount_cockatricemount_white'],
    [878, 'inv_basaliskmount'],
    [881, 'inv_suramarmount'],
    [882, 'ability_mount_viciouskorkronannihilator'],
    [883, 'inv_nightbane2mount'],
    [884, 'inv_roguemount_blue'],
    [885, 'inv_paladinmount_blue'],
    [888, 'inv_shamanmount'],
    [889, 'inv_roguemount_purple'],
    [890, 'inv_roguemount_green'],
    [891, 'inv_roguemount_red'],
    [892, 'inv_paladinmount_red'],
    [893, 'inv_paladinmount_purple'],
    [894, 'inv_paladinmount_yellow'],
    [896, 'inv_firecatmount'],
    [898, 'inv_warlockmount'],
    [899, 'inv_serpentmount_green'],
    [900, 'inv_viciousdragonturtlemount'],
    [901, 'inv_viciousdragonturtlemount'],
    [905, 'inv_suramarflyingcarpet'],
    [906, 'inv_manaraymount_black'],
    [926, 'inv_hyena2mount_light'],
    [928, 'inv_hyena2mount_tan'],
    [930, 'inv_warlockmountfire'],
    [931, 'inv_warlockmountshadow'],
    [932, 'inv_lightforgedmechsuit'],
    [933, 'inv_trilobitemount_black'],
    [934, 'inv_mount_hippogryph_arcane'],
    [935, 'inv_misc_qirajicrystal_04'],
    [936, 'inv_misc_qirajicrystal_02'],
    [937, 'inv_ridingsilithid2'],
    [939, 'inv_argustalbukmount_black'],
    [941, 'inv_moosemount2'],
    [942, 'inv_horse2green'],
    [943, 'inv_hippogryph2azsuna'],
    [944, 'inv_stormdragonmount2'],
    [945, 'inv_viciouswarfoxalliance'],
    [946, 'inv_viciouswarfoxhorde'],
    [947, 'inv_serpentmount_darkblue'],
    [948, 'inv_stormdragonmount2_fel'],
    [949, 'inv_shadowstalkerpanthermount'],
    [954, 'inv_soulhoundmount_blue'],
    [955, 'inv_argusfelstalkermount'],
    [956, 'ability_mount_bloodtick_red'],
    [958, 'inv_pterrordax2mount_white'],
    [959, 'inv_allianceshipmount'],
    [960, 'inv_hordezeppelinmount'],
    [961, 'inv_horse2purple'],
    [962, 'inv_zeppelinmount'],
    [963, 'inv_bloodtrollbeast_mount'],
    [964, 'inv_argustalbukmount_purple'],
    [965, 'inv_argustalbukmount_blue'],
    [966, 'inv_argustalbukmount_green'],
    [967, 'inv_argustalbukmount_brown'],
    [968, 'inv_argustalbukmount_red'],
    [970, 'inv_argustalbukmount_felpurple'],
    [971, 'inv_felhound3_shadow_fire'],
    [972, 'inv_felhound3_shadow_mount'],
    [973, 'inv_manaraymount_blue'],
    [974, 'inv_manaraymount_purple'],
    [975, 'inv_manaraymount_redfel'],
    [976, 'inv_manaraymount_orange'],
    [978, 'inv_mount_arcaneraven'],
    [979, 'inv_argusfelstalkermountred'],
    [980, 'inv_argusfelstalkermountgrey'],
    [981, 'inv_argusfelstalkermountblue'],
    [982, 'inv_ammo_bullet_07'],
    [983, 'inv_lightforgedelekk'],
    [984, 'inv_lightforgedelekk_amethyst'],
    [985, 'inv_lightforgedelekk_blue'],
    [986, 'inv_argustalbukmount_felred'],
    [993, 'inv_parrotmount_green'],
    [995, 'inv_parrotmount_red'],
    [996, 'inv_dressedhorse'],
    [997, 'inv_armoredraptor'],
    [999, 'inv_hovercraftmount'],
    [1006, 'inv_lightforgedelekk'],
    [1007, 'inv_hmmoosemount'],
    [1008, 'inv_nightborneracialmount'],
    [1009, 'ability_mount_voidelfstridermount'],
    [1010, 'inv_horse3saddle003_pale'],
    [1011, 'inv_dogmount'],
    [1012, 'ivn_toadloamount'],
    [1013, 'inv_bee_default'],
    [1015, 'inv_horse3saddle006_stormsong_white'],
    [1016, 'inv_horse3saddle003_black'],
    [1018, 'inv_horse3saddle008_donkey'],
    [1019, 'inv_horse3saddle003_palamino'],
    [1025, 'inv_hivemind'],
    [1026, 'inv_viciouswarbasiliskhorde'],
    [1027, 'inv_viciouswarbasiliskalliance'],
    [1028, 'achievement_dungeon_mogulrazdunk'],
    [1030, 'ability_mount_protodrakegladiatormount'],
    [1031, 'ability_mount_protodrakegladiatormount'],
    [1032, 'inv_protodrakegladiatormount_purple'],
    [1035, 'ability_mount_protodrakegladiatormount'],
    [1038, 'inv_triceratopszandalari'],
    [1039, 'inv_brontosaurusmount'],
    [1040, 'inv_armoredraptorundead'],
    [1042, 'inv_vulturemount_alabatrosswhite'],
    [1043, 'inv_pterrordax2mount_yellow'],
    [1044, 'inv_orcclanworg'],
    [1045, 'inv_vicioushordeclefthoof'],
    [1046, 'inv_dwarfpaladinram_red'],
    [1047, 'inv_dwarfpaladinram_gold'],
    [1048, 'inv_darkirondwarfcorehound'],
    [1049, 'inv_felbatmountforsaken'],
    [1050, 'inv_viciousalliancehippo'],
    [1051, 'inv_skiff'],
    [1053, 'inv_bloodtrollbeast_mount_pale'],
    [1054, 'inv_hippogryphmountnightelf'],
    [1057, 'inv_serpentmount_red'],
    [1058, 'inv_pterrordax2mount_blue'],
    [1059, 'inv_pterrordax2mount_lightgreen'],
    [1060, 'inv_pterrordax2mount_purple'],
    [1061, 'ability_mount_bloodtick_purple'],
    [1062, 'inv_misc_elitegryphonarmored'],
    [1063, 'inv_misc_elitegryphonarmored'],
    [1064, 'inv_misc_elitegryphonarmored'],
    [1166, 'inv_stingray2mount_teal'],
    [1167, 'inv_infernalmounice'],
    [1169, 'inv_misc_fish_70'],
    [1172, 'inv_trilobitemount_green'],
    [1173, 'inv_horse3_chestnut'],
    [1174, 'inv_horse3_pinto'],
    [1175, 'ability_mount_drake_twilight'],
    [1176, 'inv_misc_pet_pandaren_yeti'],
    [1178, 'achievement_moguraid_01'],
    [1179, 'ability_mount_triceratopsmount_yellow'],
    [1180, 'ability_mount_raptor_white'],
    [1182, 'inv_horse3_donkey'],
    [1183, 'ability_hunter_pet_raptor'],
    [1185, 'ability_hunter_pet_bat'],
    [1190, 'inv_horse2white'],
    [1191, 'ability_mount_fireravengodmountgreen'],
    [1192, 'inv_horse2mountelite'],
    [1193, 'inv_encrypted05'],
    [1194, 'ability_mount_warnightsaber'],
    [1195, 'ability_mount_warnightsaber'],
    [1196, 'inv_skeletalwarhorse_01_brown'],
    [1197, 'inv_skeletalwarhorse_01_purple'],
    [1198, 'inv_horsekultiran'],
    [1199, 'spell_druid_bearhug'],
    [1200, 'inv_chimera3'],
    [1201, 'ability_mount_kodo_03'],
    [1203, 'inv_nightsaber2brown'],
    [1204, 'inv_nightsaber2mountyellow'],
    [1205, 'inv_nightsaber2mount'],
    [1206, 'ivn_toadloamount'],
    [1207, 'ivn_toadloamount'],
    [1208, 'ability_mount_seahorse'],
    [1209, 'inv_misc_moosehoof_black'],
    [1210, 'ability_hunter_pet_bat'],
    [1211, 'ability_hunter_pet_bat'],
    [1212, 'inv_stormdragonmount2_fel'],
    [1213, 'ability_mount_undeadhorse'],
    [1214, 'inv_trilobitemount_blue'],
    [1215, 'inv_trilobitemount_red'],
    [1216, 'inv_saber3mount'],
    [1217, 'achievement_dungeon_coinoperatedcrowdpummeler'],
    [1218, 'inv_pterrordax2mount_bronze'],
    [1219, 'inv_waterelementalmount'],
    [1220, 'inv_crocoliskmount_blue'],
    [1221, 'inv_encrypted06'],
    [1222, 'inv_encrypted09'],
    [1223, 'inv_encrypted08'],
    [1224, 'inv_mechanicalparrotmount'],
    [1225, 'inv_zandalaripaladinmount'],
    [1227, 'inv_hunterkillershipyellow'],
    [1229, 'inv_mechagonspidertank_junker'],
    [1230, 'inv_sharkraymount_2'],
    [1231, 'inv_sharkraymount_1'],
    [1232, 'inv_sharkraymount_4'],
    [1237, 'inv_snapdragonmount01'],
    [1238, 'inv_crabmount'],
    [1239, 'inv_mechanicaltiger_grey'],
    [1240, 'inv_encrypted13'],
    [1242, 'inv_armoredelekkmount'],
    [1243, 'inv_armoredwolfmount'],
    [1245, 'inv_hordehorsemount'],
    [1246, 'inv_alliancewolfmount'],
    [1247, 'inv_mechacycle'],
    [1248, 'inv_mechacycle'],
    [1249, 'inv_triceratopsgreen'],
    [1250, 'inv_alpacamount_brown'],
    [1252, 'inv_mechagonspidertank_brass'],
    [1253, 'inv_mechagonspidertank_silver'],
    [1254, 'inv_hunterkillershipred'],
    [1255, 'inv_snapdragonmount03'],
    [1256, 'inv_snapdragonmount02'],
    [1257, 'inv_sharkraymount_3'],
    [1258, 'inv_hippocampusmount_purple'],
    [1260, 'inv_hippocampusmount_red'],
    [1262, 'inv_hippocampusmount_black'],
    [1265, 'inv_voiddragonmount'],
    [1266, 'inv_encrypted22'],
    [1267, 'inv_encrypted21'],
    [1269, 'inv_sharkraymount_1'],
    [1270, 'inv_hunterkillershipblue'],
    [1271, 'inv_misc_elitegryphonarmored'],
    [1272, 'inv_pterrordax2mount_white'],
    [1282, 'inv_nzothserpentmount_black'],
    [1283, 'inv_mechagnomestrider'],
    [1285, 'inv_frostwolfhowler'],
    [1286, 'inv_vulperamount'],
    [1287, 'inv_explorergyrocopter'],
    [1288, 'inv_camelmount2'],
    [1289, 'inv_aetherserpentmount'],
    [1290, 'inv_ratmount2'],
    [1291, 'inv_oxmount'],
    [1292, 'ability_mount_mountainram'],
    [1293, 'inv_eyeballjellyfishmount'],
    [1297, 'inv_thunderislebirdbossmount_blue'],
    [1298, 'inv_deathwargmountblack'],
    [1299, 'inv_deathwargmount2black'],
    [1302, 'inv_ardenwealdstagmount_blue'],
    [1303, 'inv_ardenwealdstagmount2_blue'],
    [1304, 'inv_jailerhoundmount_gray'],
    [1305, 'inv_decomposermountpurple'],
    [1306, 'inv_horse2ardenwealdmount_dark'],
    [1307, 'inv_horse2bastionmount_yellow'],
    [1309, 'inv_devourersmallmount_light'],
    [1310, 'inv_giantvampirebatmount_bronze'],
    [1311, 'inv_pandarenserpentmount_pink'],
    [1313, 'inv_pandarenserpentmount_white'],
    [1314, 'inv_dragonskywallmount_bronze'],
    [1315, 'inv_nzothserpentmount_red'],
    [1317, 'inv_vulturemount_black'],
    [1318, 'inv_vulturemount_red'],
    [1319, 'inv_aqirflyingmount_black'],
    [1320, 'inv_aqirflyingmount_purple'],
    [1321, 'inv_aqirflyingmount_red'],
    [1322, 'inv_nzothserpentmount_purple'],
    [1324, 'inv_alpacamount_black'],
    [1326, 'inv_nzothserpentmount_pale'],
    [1327, 'inv_quilenmount_red'],
    [1328, 'inv_quilenmount_gold'],
    [1329, 'inv_alpacamount_yellow'],
    [1332, 'inv_mothardenwealdmount_blue'],
    [1346, 'inv_encrypted16'],
    [1350, 'inv_rocmaldraxxusmountblack'],
    [1351, 'inv_viciousalliancespider'],
    [1352, 'inv_vicioushordespider'],
    [1354, 'inv_ardenwealdstagmount_dark'],
    [1355, 'inv_ardenwealdstagmount_teal'],
    [1356, 'inv_ardenwealdstagmount_white'],
    [1357, 'inv_ardenwealdstagmount2_blue'],
    [1358, 'inv_ardenwealdstagmount2_blue'],
    [1359, 'inv_ardenwealdstagmount2_blue'],
    [1360, 'inv_horse2ardenwealdmount_blue'],
    [1361, 'inv_mothardenwealdmount_dark'],
    [1362, 'inv_decomposermountyellow'],
    [1363, 'inv_shadebeastmount'],
    [1364, 'inv_giantbeastmount_blue'],
    [1365, 'inv_giantbeastmount_green'],
    [1366, 'inv_giantbeastmount'],
    [1367, 'inv_giantbeastmount_orange'],
    [1368, 'inv_giantbeastmount2_blue'],
    [1369, 'inv_giantbeastmount2_green'],
    [1370, 'inv_giantbeastmount2'],
    [1371, 'inv_giantbeastmount2_orange'],
    [1372, 'inv_maldraxxusboarmount_black'],
    [1373, 'inv_maldraxxusboarmount_green'],
    [1375, 'inv_maldraxxusboarmount_purple'],
    [1376, 'inv_giantvampirebatmount_silver'],
    [1377, 'inv_giantvampirebatmount_white'],
    [1378, 'inv_giantvampirebatmount_purple'],
    [1379, 'inv_devourersmallmount_dark'],
    [1382, 'inv_deathwargmountpurple'],
    [1384, 'inv_deathwargmountred'],
    [1385, 'inv_deathwargmountwhite'],
    [1387, 'inv_deathwargmount2purple'],
    [1388, 'inv_deathwargmount2white'],
    [1389, 'inv_deathwargmount2red'],
    [1391, 'achievement_dungeon_sanguinedepths_kryxis'],
    [1392, 'inv_decomposermountwhite'],
    [1393, 'inv_fox2_green'],
    [1394, 'inv_automatonlionmount_black'],
    [1395, 'inv_automatonlionmount_bronze'],
    [1396, 'inv_automatonlionmount'],
    [1397, 'inv_ardenwealdpod'],
    [1398, 'inv_automatonlionmount_silver'],
    [1399, 'inv_automatonlionmount_silver'],
    [1400, 'inv_automatonlionmount2'],
    [1401, 'inv_automatonlionmount2_black'],
    [1402, 'inv_automatonlionmount2_bronze'],
    [1404, 'inv_wingedlion2mount_silver'],
    [1406, 'inv_maldraxxusflyermount_red'],
    [1407, 'inv_maldraxxusflyermount_green'],
    [1408, 'inv_maldraxxusflyermount_blue'],
    [1409, 'inv_rocmaldraxxusmountwhite'],
    [1410, 'inv_rocmaldraxxusmountpurple'],
    [1411, 'inv_rocmaldraxxusmountgreen'],
    [1413, 'inv_horse2bastionmount_purple'],
    [1414, 'inv_horse3saddle001_evil'],
    [1415, 'inv_toadardenwealdmount'],
    [1419, 'inv_deathelementalmount_black'],
    [1420, 'inv_decomposermountblack'],
    [1421, 'inv_horse3saddle003_evil'],
    [1422, 'inv_darkhoundmount_draka_blue'],
    [1423, 'inv_wingedlion2mount_dark'],
    [1424, 'inv_bearmountblizzard'],
    [1425, 'inv_wingedlion2mount'],
    [1426, 'inv_horse2bastionmount_blue'],
    [1428, 'inv_mothardenwealdmount_red'],
    [1429, 'inv_mothardenwealdmount_mint'],
    [1436, 'inv_automatonfliermount_copper'],
    [1437, 'inv_darkhoundmount_draka'],
    [1438, 'inv_manaraymount_orange'],
    [1439, 'inv_manaraymount_black'],
    [1440, 'inv_manaraymount_blackfel'],
    [1441, 'inv_jailerhoundmount_white'],
    [1442, 'inv_jailerhoundmount_black'],
    [1443, 'inv_devourermediummount'],
    [1444, 'inv_warpstalkermount'],
    [1445, 'inv_nzothserpentmount_abomination'],
    [1446, 'inv_brokermount_brass'],
    [1449, 'inv_flymaldraxxusmount_black'],
    [1450, 'inv_mawexpansionfliermountyellow'],
    [1454, 'inv_devourerswarmer_blue'],
    [1455, 'inv_mawexpansionbearmount_green'],
    [1458, 'inv_ancientmount'],
    [1459, 'inv_vicioushordegorm'],
    [1460, 'inv_viciousalliancegorm'],
    [1471, 'inv_dragonhawkmountshadowlands'],
    [1475, 'inv_mawguardhandmountpurple'],
    [1476, 'inv_decomposermountgreen'],
    [1477, 'inv_darkhoundmount_draka_orange'],
    [1480, 'inv_shadebeastmount_blue'],
    [1481, 'inv_brokermount_dark'],
    [1484, 'inv_wolfserpentmountpurple'],
    [1485, 'inv_wolfserpentmountyellow'],
    [1486, 'inv_wolfserpentmountwhite'],
    [1487, 'inv_wolfserpentmountgreen'],
    [1489, 'inv_gargoylebrute2mount_dark'],
    [1490, 'inv_gargoylebrute2mount_gray'],
    [1491, 'inv_gargoylebrute2mount_pale'],
    [1492, 'inv_automatonfliermount'],
    [1493, 'inv_automatonfliermount_dark'],
    [1494, 'inv_automatonfliermount_silver'],
    [1495, 'inv_flymaldraxxusmount_green'],
    [1496, 'inv_flymaldraxxusmount_purple'],
    [1497, 'inv_flymaldraxxusmount_copper'],
    [1503, 'inv_mawguardhandmountgold'],
    [1504, 'inv_mawguardhandmountblack'],
    [1505, 'inv_mawexpansionbearmount_yellow'],
    [1506, 'inv_mawexpansionbearmount_red'],
    [1507, 'inv_mawexpansionbearmount_purple'],
    [1508, 'inv_mawexpansionfliermountgreen'],
    [1509, 'inv_mawexpansionfliermountred'],
    [1510, 'inv_mawexpansionfliermountpurple'],
    [1511, 'inv_horse2ardenwealdmount_doe'],
    [1513, 'inv_ratmounthearthstone'],
    [1514, 'inv_devourerswarmermount_dark'],
    [1520, 'inv_deathelementalmount_green'],
    [803, 'inv_gargoylebrute2mount_brown'],
    [1330, 'inv_catmount'],
    [1416, 'ability_mount_mawhorsespikes_blue'],
    [1417, 'inv_mawguardhandmountblue'],
    [1456, 'inv_phoenix2mount_blue'],
    [1500, 'ability_mount_mawhorsespikes_purple'],
    [1501, 'ability_mount_mawhorsespikes_teal'],
    [1502, 'ability_mount_mawhorsespikes_yellow'],
]

p = requests.Session()
retries = Retry(total=3, backoff_factor=1)
p.mount('https://', HTTPAdapter(max_retries=retries))


def limit_call(url, params):
    try:
        response = p.get(url, params=params, timeout=5)
        return response
    except requests.exceptions.RequestException as e:
        temp_response = {'status_code': 999}
        response = SimpleNamespace(**temp_response)
        return response


@shared_task
def add(x, y):
    return x + y


@shared_task
def fullAltScan(user, client, secret):
    counter = 0
    alts = []
    all_alts = ProfileAlt.objects.all()
    old_alts = all_alts.filter(user=user)
    for alt in old_alts:
        alts.append(alt.altId)
    total = len(alts)
    user_obj = ProfileUser.objects.get(userId=user)
    user_obj.userLastUpdate = timezone.now()
    user_obj.save()
    for index, alt in enumerate(alts, start=1):
        print(counter)
        print('Processing: {} of {}'.format(index, total))
        alt_obj = ProfileAlt.objects.get(altId=alt)
        # if alt_obj.altName != 'Fazziest':
        #     continue
        realm = alt_obj.altRealmSlug
        name = alt_obj.altName.lower()
        url = 'https://eu.battle.net/oauth/token?grant_type=client_credentials'
        params = {'client_id': client, 'client_secret': secret}
        x = requests.post(url, data=params)
        counter += 1
        try:
            token = x.json()['access_token']
            urls = [
                'https://eu.api.blizzard.com/profile/wow/character/' + realm + '/' + name + '/professions',
                'https://eu.api.blizzard.com/profile/wow/character/' + realm + '/' + name + '/equipment',
                'https://eu.api.blizzard.com/profile/wow/character/' + realm + '/' + name + '/collections/mounts',
            ]
            myobj = {'access_token': token, 'namespace': 'profile-eu', 'locale': 'en_US'}
            dataobj = {'access_token': token, 'locale': 'en_US'}
            for url in urls:
                y = p.get(url, params=myobj, timeout=5)
                counter += 1
                if y.status_code == 200:
                    if 'professions' in url:
                        print('profession pending')
                        alt_profs = []
                        try:
                            prof_obj = ProfileAltProfession.objects.get(alt=alt_obj)
                        except ProfileAltProfession.DoesNotExist:
                            prof_obj = ProfileAltProfession.objects.create(
                                alt=alt_obj,
                                profession1=0,
                                profession2=0,
                                altProfessionExpiryDate=timezone.now() + datetime.timedelta(days=30)
                            )
                        try:
                            data = y.json()['primaries']
                            for prof in data:
                                alt_profs.append(prof['profession']['id'])
                                try:
                                    obj = DataProfession.objects.get(professionId=prof['profession']['id'])
                                except DataProfession.DoesNotExist:
                                    print('Does not exist: {}'.format(prof['profession']['name']))
                                for tier in prof['tiers']:
                                    try:
                                        obj1 = DataProfessionTier.objects.get(tierId=tier['tier']['id'])
                                    except DataProfessionTier.DoesNotExist:
                                        print('Does not exist: {}'.format(tier['tier']['name']))
                                    try:
                                        for recipe in tier['known_recipes']:
                                            try:
                                                obj2 = DataProfessionRecipe.objects.get(recipeId=recipe['id'])
                                            except DataProfessionRecipe.DoesNotExist:
                                                print('Does not exist: {}'.format(recipe['name']))

                                                recipe_response = limit_call(recipe['key']['href'], params=dataobj)
                                                counter += 1
                                                if recipe_response.status_code == 200:
                                                    try:
                                                        recipe_details = recipe_response.json()
                                                        try:
                                                            rank = recipe_details['rank']
                                                        except KeyError as e:
                                                            rank = 1
                                                        try:
                                                            crafted_quantity = recipe_details['crafted_quantity']['value']
                                                        except KeyError as e:
                                                            crafted_quantity = 1
                                                        try:
                                                            description = recipe_details['description']
                                                        except KeyError as e:
                                                            description = 'None'
                                                        obj2 = DataProfessionRecipe.objects.create(
                                                            tier=obj1,
                                                            recipeId=recipe_details['id'],
                                                            recipeName=recipe_details['name'],
                                                            recipeDescription=description,
                                                            recipeCategory='N/A',
                                                            recipeRank=rank,
                                                            recipeCraftedQuantity=crafted_quantity
                                                        )
                                                    except KeyError as e:
                                                        pass
                                            try:
                                                obj3 = ProfileAltProfessionData.objects.get(alt=prof_obj, profession=obj, professionTier=obj1, professionRecipe=obj2)
                                                obj3.altProfessionDataExpiryDate = timezone.now() + datetime.timedelta(days=30)
                                                obj3.save()
                                            except ProfileAltProfessionData.DoesNotExist:
                                                obj3 = ProfileAltProfessionData.objects.create(
                                                    alt=prof_obj,
                                                    profession=obj,
                                                    professionTier=obj1,
                                                    professionRecipe=obj2,
                                                    altProfessionDataExpiryDate=timezone.now() + datetime.timedelta(days=30)
                                                )
                                    except KeyError as e:
                                        pass
                        except KeyError as e:
                            pass
                        while len(alt_profs) < 2:
                            alt_profs.append(0)
                        old_alt_profs = [prof_obj.profession1, prof_obj.profession2]
                        for prof in old_alt_profs:
                            if prof not in alt_profs:
                                ProfileAltProfessionData.objects.filter(alt=prof_obj, profession=prof).delete()
                        prof_obj.profession1 = alt_profs[0]
                        prof_obj.profession2 = alt_profs[1]
                        prof_obj.altProfessionExpiryDate = timezone.now() + datetime.timedelta(days=30)
                        prof_obj.save()
                    elif 'equipment' in url:
                        print('equipment pending')
                        alt_equipment = {}
                        try:
                            alt_equip_obj = ProfileAltEquipment.objects.get(alt=alt_obj)
                        except ProfileAltEquipment.DoesNotExist:
                            alt_equip_obj = ProfileAltEquipment.objects.create(
                                alt=alt_obj,
                                head=0,
                                neck=0,
                                shoulder=0,
                                back=0,
                                chest=0,
                                tabard=0,
                                shirt=0,
                                wrist=0,
                                hands=0,
                                belt=0,
                                legs=0,
                                feet=0,
                                ring1=0,
                                ring2=0,
                                trinket1=0,
                                trinket2=0,
                                weapon1=0,
                                weapon2=0,
                                altEquipmentExpiryDate=timezone.now() + datetime.timedelta(days=30)
                            )
                        try:
                            data = y.json()['equipped_items']
                            for item in data:
                                try:
                                    obj = DataEquipment.objects.get(equipmentId=item['item']['id'])
                                except DataEquipment.DoesNotExist:
                                    obj = DataEquipment.objects.create(
                                        equipmentId=item['item']['id'],
                                        equipmentName=item['name'],
                                        equipmentType=item['item_subclass']['name'],
                                        equipmentSlot=item['slot']['name'],
                                        equipmentIcon='not done yet'
                                    )
                                variantCode = ''
                                try:
                                    for bonus in item['bonus_list']:
                                        variantCode += str(bonus)
                                except KeyError:
                                    variantCode = 'FLUFF'
                                try:
                                    obj1 = DataEquipmentVariant.objects.get(equipment=obj, variant=variantCode)
                                except DataEquipmentVariant.DoesNotExist:
                                    stamina = strength = agility = intellect = haste = mastery = vers = crit = 0
                                    try:
                                        for stat in item['stats']:
                                            if stat['type']['type'] == 'STAMINA':
                                                stamina = stat['value']
                                            elif stat['type']['type'] == 'STRENGTH':
                                                strength = stat['value']
                                            elif stat['type']['type'] == 'AGILITY':
                                                agility = stat['value']
                                            elif stat['type']['type'] == 'INTELLECT':
                                                intellect = stat['value']
                                            elif stat['type']['type'] == 'HASTE_RATING':
                                                haste = stat['value']
                                            elif stat['type']['type'] == 'MASTERY_RATING':
                                                mastery = stat['value']
                                            elif stat['type']['type'] == 'VERSATILITY':
                                                vers = stat['value']
                                            elif stat['type']['type'] == 'CRIT_RATING':
                                                crit = stat['value']
                                    except KeyError:
                                        pass
                                    try:
                                        armour = item['armor']['value']
                                    except KeyError:
                                        armour = 0
                                    obj1 = DataEquipmentVariant.objects.create(
                                        equipment=obj,
                                        variant=variantCode,
                                        stamina=stamina,
                                        armour=armour,
                                        strength=strength,
                                        agility=agility,
                                        intellect=intellect,
                                        haste=haste,
                                        mastery=mastery,
                                        vers=vers,
                                        crit=crit,
                                        level=item['level']['value'],
                                        quality=item['quality']['name']
                                    )
                                alt_equipment[item['slot']['name'].lower()] = str(item['item']['id']) + ':' + variantCode
                        except KeyError as e:
                            print(e)
                        setattr(alt_equip_obj, 'head', alt_equipment.get('head') or 0)
                        setattr(alt_equip_obj, 'neck', alt_equipment.get('neck') or 0)
                        setattr(alt_equip_obj, 'shoulder', alt_equipment.get('shoulders') or 0)
                        setattr(alt_equip_obj, 'back', alt_equipment.get('back') or 0)
                        setattr(alt_equip_obj, 'chest', alt_equipment.get('chest') or 0)
                        setattr(alt_equip_obj, 'tabard', alt_equipment.get('tabard') or 0)
                        setattr(alt_equip_obj, 'shirt', alt_equipment.get('shirt') or 0)
                        setattr(alt_equip_obj, 'wrist', alt_equipment.get('wrist') or 0)
                        setattr(alt_equip_obj, 'hands', alt_equipment.get('hands') or 0)
                        setattr(alt_equip_obj, 'belt', alt_equipment.get('waist') or 0)
                        setattr(alt_equip_obj, 'legs', alt_equipment.get('legs') or 0)
                        setattr(alt_equip_obj, 'feet', alt_equipment.get('feet') or 0)
                        setattr(alt_equip_obj, 'ring1', alt_equipment.get('ring 1') or 0)
                        setattr(alt_equip_obj, 'ring2', alt_equipment.get('ring 2') or 0)
                        setattr(alt_equip_obj, 'trinket1', alt_equipment.get('trinket 1') or 0)
                        setattr(alt_equip_obj, 'trinket2', alt_equipment.get('trinket 2') or 0)
                        setattr(alt_equip_obj, 'weapon1', alt_equipment.get('main hand') or 0)
                        setattr(alt_equip_obj, 'weapon2', alt_equipment.get('off hand') or 0)
                        alt_equip_obj.save()
                    elif 'mounts' in url:
                        print('mounts pending')
                        try:
                            data = y.json()['mounts']
                            for mount in data:
                                try:
                                    mount_obj = DataMount.objects.get(mountId=mount['mount']['id'])
                                except DataMount.DoesNotExist:
                                    print('Mount does not exist: {} - {}'.format(mount['mount']['id'], mount['mount']['name']))
                                try:
                                    obj = ProfileUserMount.objects.get(user=user_obj, mount=mount_obj)
                                except ProfileUserMount.DoesNotExist:
                                    obj = ProfileUserMount.objects.create(
                                        user=user_obj,
                                        mount=mount_obj
                                    )
                        except KeyError as e:
                            print(e)
                    else:
                        print('donebutnotdone')
        except Exception as e:
            print(e)


@shared_task
def fullDataScan(client, secret):
    url = 'https://eu.battle.net/oauth/token?grant_type=client_credentials'
    params = {'client_id': client, 'client_secret': secret}
    x = requests.post(url, data=params)
    try:
        token = x.json()['access_token']
        urls = [
            'https://eu.api.blizzard.com/data/wow/profession/index',
            'https://eu.api.blizzard.com/data/wow/mount/index',
        ]
        dataobj = {'access_token': token, 'namespace': 'static-eu', 'locale': 'en_US'}
        for url in urls:
            y = limit_call(url, params=dataobj)
            if y.status_code == 200:
                if 'profession' in url:
                    try:
                        profession_index = y.json()['professions']
                        for profession in profession_index:
                            # if profession['name'] != 'Mining':
                            #     continue
                            profession_response = limit_call(profession['key']['href'], params=dataobj)
                            if profession_response.status_code == 200:
                                try:
                                    profession_details = profession_response.json()
                                    try:
                                        obj_profession = DataProfession.objects.get(professionId=profession_details['id'])
                                    except DataProfession.DoesNotExist:
                                        obj_profession = DataProfession.objects.create(
                                            professionId=profession_details['id'],
                                            professionName=profession_details['name'],
                                            professionDescription=profession_details['description']
                                        )
                                except KeyError as e:
                                    print(e)
                                try:
                                    tier_index = profession_details['skill_tiers']
                                    for tier in tier_index:
                                        print('Processing tier: {}'.format(tier['name']))
                                        tier_response = limit_call(tier['key']['href'], params=dataobj)
                                        if tier_response.status_code == 200:
                                            try:
                                                tier_details = tier_response.json()
                                                try:
                                                    obj_tier = DataProfessionTier.objects.get(tierId=tier_details['id'])
                                                except DataProfessionTier.DoesNotExist:
                                                    obj_tier = DataProfessionTier.objects.create(
                                                        profession=obj_profession,
                                                        tierId=tier_details['id'],
                                                        tierName=tier_details['name'],
                                                        tierMinSkill=tier_details['minimum_skill_level'],
                                                        tierMaxSkill=tier_details['maximum_skill_level']
                                                    )
                                            except KeyError as e:
                                                print(e)
                                            try:
                                                category_index = tier_details['categories']
                                                for category in category_index:
                                                    print('Processing category: {}'.format(category['name']))
                                                    try:
                                                        recipe_index = category['recipes']
                                                        for recipe in recipe_index:
                                                            print('Processing recipe: {}'.format(recipe['name']))
                                                            recipe_response = limit_call(recipe['key']['href'], params=dataobj)
                                                            if recipe_response.status_code == 200:
                                                                try:
                                                                    recipe_details = recipe_response.json()
                                                                    try:
                                                                        obj_recipe = DataProfessionRecipe.objects.get(recipeId=recipe_details['id'])
                                                                    except DataProfessionRecipe.DoesNotExist:
                                                                        try:
                                                                            rank = recipe_details['rank']
                                                                        except KeyError as e:
                                                                            rank = 1
                                                                        try:
                                                                            crafted_quantity = recipe_details['crafted_quantity']['value']
                                                                        except KeyError as e:
                                                                            crafted_quantity = 1
                                                                        try:
                                                                            description = recipe_details['description']
                                                                        except KeyError as e:
                                                                            description = 'None'
                                                                        obj_recipe = DataProfessionRecipe.objects.create(
                                                                            tier=obj_tier,
                                                                            recipeId=recipe_details['id'],
                                                                            recipeName=recipe_details['name'],
                                                                            recipeDescription=description,
                                                                            recipeCategory=category['name'],
                                                                            recipeRank=rank,
                                                                            recipeCraftedQuantity=crafted_quantity
                                                                        )
                                                                except KeyError as e:
                                                                    print(e)
                                                                try:
                                                                    reagent_index = recipe_details['reagents']
                                                                    for reagent in reagent_index:
                                                                        reagent_response = limit_call(reagent['reagent']['key']['href'], params=dataobj)
                                                                        if reagent_response.status_code == 200:
                                                                            try:
                                                                                reagent_details = reagent_response.json()
                                                                                try:
                                                                                    obj_reagent = DataReagent.objects.get(reagentId=reagent_details['id'])
                                                                                except DataReagent.DoesNotExist:
                                                                                    reagent_media_response = limit_call(reagent_details['media']['key']['href'], params=dataobj)
                                                                                    if reagent_media_response.status_code == 200:
                                                                                        try:
                                                                                            media = reagent_media_response.json()['assets'][0]['value']
                                                                                        except KeyError as e:
                                                                                            media = 'Not Found'
                                                                                    else:
                                                                                        print(reagent_media_response.status_code)
                                                                                    obj_reagent = DataReagent.objects.create(
                                                                                        reagentId=reagent_details['id'],
                                                                                        reagentName=reagent_details['name'],
                                                                                        reagentQuality=reagent_details['quality']['name'],
                                                                                        reagentMedia=media
                                                                                    )
                                                                            except KeyError as e:
                                                                                print(e)
                                                                            try:
                                                                                obj_recipereagent = DataRecipeReagent.objects.get(recipe=obj_recipe, reagent=obj_reagent)
                                                                            except DataRecipeReagent.DoesNotExist:
                                                                                obj_recipereagent = DataRecipeReagent.objects.create(
                                                                                    recipe=obj_recipe,
                                                                                    reagent=obj_reagent,
                                                                                    quantity=reagent['quantity']
                                                                                )
                                                                        else:
                                                                            print(reagent_response.status_code)
                                                                except KeyError as e:
                                                                    print(e)
                                                            else:
                                                                print(recipe_response.status_code)
                                                    except KeyError as e:
                                                        print(e)
                                            except KeyError as e:
                                                print(e)
                                        else:
                                            print(tier_response.status_code)
                                except KeyError as e:
                                    print(e)
                            else:
                                print(profession_response.status_code)
                    except KeyError as e:
                        print(e)
                elif 'mount' in url:
                    try:
                        mount_index = y.json()['mounts']
                        for mount in mount_index:
                            print(mount['name'])
                            mount_response = limit_call(mount['key']['href'], params=dataobj)
                            if mount_response.status_code == 200:
                                try:
                                    mount_details = mount_response.json()
                                    try:
                                        obj_mount = DataMount.objects.get(mountId=mount_details['id'])
                                    except DataMount.DoesNotExist:
                                        mount_media_response = limit_call(mount_details['creature_displays'][0]['key']['href'], params=dataobj)
                                        if mount_media_response.status_code == 200:
                                            try:
                                                media_zoom = mount_media_response.json()['assets'][0]['value']
                                            except KeyError as e:
                                                media_zoom = 'Not Found'
                                        else:
                                            print(mount_media_response.status_code)
                                        media_icon = 'https://render.worldofwarcraft.com/eu/icons/56/inv_misc_questionmark.jpg'
                                        for item in item_search_details:
                                            try:
                                                if mount_details['id'] == item[0]:
                                                    media_icon = 'https://render.worldofwarcraft.com/eu/icons/56/' + item[1] + '.jpg'
                                                    break
                                            except KeyError as e:
                                                print(e)
                                        try:
                                            faction = mount_details['faction']['name']
                                        except KeyError as e:
                                            faction = 'N/A'
                                        try:
                                            source = mount_details['source']['name']
                                        except KeyError as e:
                                            source = 'N/A'
                                        try:
                                            description = mount_details['description']
                                        except KeyError as e:
                                            description = 'None'
                                        if description is None:
                                            description = 'None'
                                        obj_mount = DataMount.objects.create(
                                            mountId=mount_details['id'],
                                            mountName=mount_details['name'],
                                            mountDescription=description,
                                            mountSource=source,
                                            mountMediaZoom=media_zoom,
                                            mountMediaIcon=media_icon,
                                            mountFaction=faction
                                        )
                                except KeyError as e:
                                    print(e)
                            else:
                                print(mount_response.status_code)
                    except KeyError as e:
                        print(e)
            else:
                print(y.status_code)
    except KeyError as e:
        print(e)
    return('Done Long Task')
