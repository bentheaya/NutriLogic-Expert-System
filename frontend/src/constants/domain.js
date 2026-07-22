/**
 * Domain vocabulary mirrored from backend/nutrition/domain.py.
 * Keep in sync when adding conditions or symptoms.
 */

export const CONDITIONS = [
  { value: "healthy", label: "Healthy (general)" },
  { value: "hypertension", label: "Hypertension" },
  { value: "type2_diabetes", label: "Type 2 Diabetes" },
  { value: "anaemia", label: "Anaemia" },
  { value: "vitA_deficiency", label: "Vitamin A Deficiency" },
  { value: "rickets", label: "Rickets / Vitamin D Deficiency" },
];

export const SYMPTOMS = [
  { value: "fatigue", label: "Fatigue / tiredness" },
  { value: "pale_skin", label: "Pale skin" },
  { value: "night_blindness", label: "Night blindness" },
  { value: "dry_skin", label: "Dry skin" },
  { value: "frequent_infections", label: "Frequent infections" },
  { value: "bone_pain", label: "Bone pain" },
  { value: "muscle_weakness", label: "Muscle weakness" },
  { value: "rickets", label: "Rickets (bowing of legs)" },
  { value: "mouth_sores", label: "Mouth sores" },
  { value: "muscle_cramps", label: "Muscle cramps" },
];

export const ACTIVITY_OPTIONS = [
  { value: "sedentary", label: "Sedentary" },
  { value: "light", label: "Lightly Active" },
  { value: "moderate", label: "Moderately Active" },
  { value: "active", label: "Active" },
  { value: "very_active", label: "Very Active" },
];
