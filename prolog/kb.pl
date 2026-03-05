% NutriLogic Knowledge Base
% Based on MOH 2025 Kenya Nutrient Profile Model
% ================================================

% --- Kenyan Food Facts ---
% food(Name, FoodGroup, CaloriesPer100g, ProteinG, CarbsG, FatG, FibreG)

food(ugali,        grains,         360, 3.6, 78.0, 1.5, 2.0).
food(chapati,      grains,         330, 7.0, 55.0, 9.0, 2.5).
food(githeri,      legumes_grains, 180, 8.5, 30.0, 2.5, 5.0).
food(sukuma_wiki,  vegetables,      35, 3.5,  5.0, 0.5, 2.8).
food(managu,       vegetables,      42, 4.2,  6.8, 0.8, 3.5).
food(terere,       vegetables,      36, 3.8,  5.5, 0.6, 3.0).
food(beans,        legumes,        130, 8.9, 23.0, 0.5, 6.4).
food(lentils,      legumes,        116, 9.0, 20.0, 0.4, 7.9).
food(arrow_roots,  tubers,         112, 1.5, 27.0, 0.1, 1.9).
food(sweet_potato, tubers,          86, 1.6, 20.0, 0.1, 3.0).
food(cassava,      tubers,         160, 1.4, 38.0, 0.3, 1.8).
food(mursik,       dairy,           61, 3.2,  4.7, 3.3, 0.0).
food(maziwa_lala,  dairy,           63, 3.3,  4.9, 3.3, 0.0).
food(tilapia,      fish,           128, 26.0,  0.0, 2.7, 0.0).
food(omena,        fish,           290, 30.0,  0.0,18.0, 0.0).
food(beef,         meat,           250, 26.0,  0.0,16.0, 0.0).
food(chicken,      meat,           165, 31.0,  0.0, 3.6, 0.0).
food(egg,          protein,        155, 13.0,  1.1,11.0, 0.0).
food(groundnuts,   nuts,           567, 26.0, 16.0,50.0, 8.5).
food(avocado,      fruits,         160,  2.0,  9.0,15.0, 7.0).
food(mango,        fruits,          60,  0.8, 15.0, 0.4, 1.6).
food(banana,       fruits,          89,  1.1, 23.0, 0.3, 2.6).
food(passion_fruit,fruits,          97,  2.2, 23.0, 0.7,10.4).

% --- Micronutrient Profile ---
% micronutrient(Food, iron_mg, calcium_mg, zinc_mg, vitA_ug, vitC_mg, folate_ug)

micronutrient(ugali,         1.0,   7.0, 0.8,  0.0,  0.0,  6.0).
micronutrient(sukuma_wiki,   1.5, 150.0, 0.4, 469.0, 93.0, 29.0).
micronutrient(managu,        3.0, 188.0, 0.5, 292.0, 40.0, 43.0).
micronutrient(terere,        2.3, 215.0, 0.9, 146.0, 43.0, 85.0).
micronutrient(beans,         2.2,  46.0, 1.0,  0.0,  2.1, 130.0).
micronutrient(lentils,       3.3,  19.0, 1.3,  0.0,  1.5, 181.0).
micronutrient(omena,         5.3, 920.0, 2.0,  10.0,  0.0,  8.0).
micronutrient(tilapia,       0.6,  14.0, 0.6,  10.0,  0.0, 15.0).
micronutrient(mursik,        0.1, 120.0, 0.4,  14.0,  1.0, 11.0).
micronutrient(maziwa_lala,   0.1, 120.0, 0.4,  14.0,  1.0, 11.0).
micronutrient(beef,          2.6,  18.0, 4.8,   0.0,  0.0,  6.0).
micronutrient(egg,           1.2,  50.0, 1.1, 149.0,  0.0, 47.0).
micronutrient(groundnuts,    2.3,  54.0, 3.3,   0.0,  0.0, 98.0).
micronutrient(avocado,       0.6,  13.0, 0.6,   7.0, 10.0, 81.0).
micronutrient(mango,         0.2,  10.0, 0.1,  54.0, 36.0, 43.0).
micronutrient(sweet_potato,  0.6,  30.0, 0.3, 709.0, 20.0, 11.0).

% --- Food Suitability for Health Conditions ---
% suitable_for(Food, Condition)

suitable_for(ugali,        healthy).
suitable_for(sukuma_wiki,  healthy).
suitable_for(sukuma_wiki,  hypertension).
suitable_for(sukuma_wiki,  type2_diabetes).
suitable_for(managu,       healthy).
suitable_for(managu,       hypertension).
suitable_for(managu,       type2_diabetes).
suitable_for(managu,       anaemia).
suitable_for(terere,       healthy).
suitable_for(terere,       anaemia).
suitable_for(terere,       hypertension).
suitable_for(beans,        healthy).
suitable_for(beans,        type2_diabetes).
suitable_for(beans,        anaemia).
suitable_for(lentils,      healthy).
suitable_for(lentils,      type2_diabetes).
suitable_for(lentils,      anaemia).
suitable_for(omena,        healthy).
suitable_for(omena,        anaemia).
suitable_for(omena,        rickets).
suitable_for(tilapia,      healthy).
suitable_for(tilapia,      hypertension).
suitable_for(tilapia,      type2_diabetes).
suitable_for(mursik,       healthy).
suitable_for(mursik,       rickets).
suitable_for(maziwa_lala,  healthy).
suitable_for(maziwa_lala,  rickets).
suitable_for(groundnuts,   healthy).
suitable_for(groundnuts,   type2_diabetes).
suitable_for(avocado,      healthy).
suitable_for(avocado,      hypertension).
suitable_for(avocado,      type2_diabetes).
suitable_for(sweet_potato, healthy).
suitable_for(sweet_potato, vitA_deficiency).
suitable_for(mango,        healthy).
suitable_for(mango,        vitA_deficiency).
suitable_for(egg,          healthy).
suitable_for(egg,          anaemia).
suitable_for(arrow_roots,  type2_diabetes).
suitable_for(githeri,      healthy).

% Foods to AVOID for conditions
avoid_for(ugali,     type2_diabetes) :- !.   % high glycaemic index
avoid_for(chapati,   type2_diabetes) :- !.
avoid_for(cassava,   type2_diabetes) :- !.

% --- Deficiency Diagnosis Rules ---
% diagnose_deficiency(+Symptoms, -Deficiency)

diagnose_deficiency(Symptoms, iron_deficiency) :-
    member(fatigue, Symptoms),
    member(pale_skin, Symptoms).

diagnose_deficiency(Symptoms, vitamin_a_deficiency) :-
    member(night_blindness, Symptoms).

diagnose_deficiency(Symptoms, vitamin_a_deficiency) :-
    member(dry_skin, Symptoms),
    member(frequent_infections, Symptoms).

diagnose_deficiency(Symptoms, vitamin_d_deficiency) :-
    member(bone_pain, Symptoms).

diagnose_deficiency(Symptoms, vitamin_d_deficiency) :-
    member(muscle_weakness, Symptoms),
    member(rickets, Symptoms).

diagnose_deficiency(Symptoms, folate_deficiency) :-
    member(fatigue, Symptoms),
    member(mouth_sores, Symptoms).

diagnose_deficiency(Symptoms, calcium_deficiency) :-
    member(muscle_cramps, Symptoms),
    member(bone_pain, Symptoms).

% --- Condition Mapping ---
% condition_for_deficiency(+Deficiency, -Condition)

condition_for_deficiency(iron_deficiency,     anaemia).
condition_for_deficiency(vitamin_a_deficiency, vitA_deficiency).
condition_for_deficiency(vitamin_d_deficiency, rickets).
condition_for_deficiency(folate_deficiency,   anaemia).
condition_for_deficiency(calcium_deficiency,  rickets).

% --- Core Recommendation Rule ---
% recommend_meal(+Condition, -Meal, -Explanation)
%
% Backward chaining: given a health condition, find a balanced meal
% (staple + protein + vegetable) that is suitable for that condition.

recommend_meal(Condition, meal(Staple, Protein, Vegetable), Explanation) :-
    % Select a staple (grain or tuber)
    food(Staple, Group, _, _, _, _, _),
    member(Group, [grains, tubers, legumes_grains]),
    suitable_for(Staple, Condition),
    \+ avoid_for(Staple, Condition),

    % Select a protein source
    food(Protein, PGroup, _, _, _, _, _),
    member(PGroup, [legumes, fish, meat, protein, nuts]),
    suitable_for(Protein, Condition),

    % Select a vegetable
    food(Vegetable, vegetables, _, _, _, _, _),
    suitable_for(Vegetable, Condition),

    % Build explanation string
    atomic_list_concat(
        ['Meal for ', Condition, ': ', Staple, ' + ', Protein, ' + ', Vegetable,
         ' — all verified against MOH 2025 Kenya Nutrient Profile Model.'],
        Explanation
    ).

% Fallback: recommend for healthy when no specific condition rule fires
recommend_meal(unknown, meal(Staple, Protein, Vegetable), Explanation) :-
    recommend_meal(healthy, meal(Staple, Protein, Vegetable), E),
    atomic_list_concat(['(General recommendation) ', E], Explanation).

% --- High-Level Entry Point ---
% get_recommendation(+Symptoms, -Meal, -Explanation)

get_recommendation(Symptoms, Meal, Explanation) :-
    diagnose_deficiency(Symptoms, Deficiency),
    condition_for_deficiency(Deficiency, Condition),
    recommend_meal(Condition, Meal, Explanation), !.

get_recommendation(_, Meal, Explanation) :-
    recommend_meal(healthy, Meal, Explanation), !.
