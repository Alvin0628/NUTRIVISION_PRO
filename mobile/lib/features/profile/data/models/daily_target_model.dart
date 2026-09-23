class DailyTarget {
  final double calories;
  final double proteinG;
  final double carbsG;
  final double fatG;
  final double fiberG;
  final double omega3G;
  final double magnesiumMg;
  final double zincMg;
  final double ironMg;
  final double calciumMg;
  final double vitaminCMg;
  final double vitaminBComplexMg;
  final double vitaminDMcg;
  final double vitaminB12Mcg;
  final double vitaminAMcg;
  final double folicAcidMcg;

  DailyTarget({
    required this.calories,
    required this.proteinG,
    required this.carbsG,
    required this.fatG,
    required this.fiberG,
    required this.omega3G,
    required this.magnesiumMg,
    required this.zincMg,
    required this.ironMg,
    required this.calciumMg,
    required this.vitaminCMg,
    required this.vitaminBComplexMg,
    required this.vitaminDMcg,
    required this.vitaminB12Mcg,
    required this.vitaminAMcg,
    required this.folicAcidMcg,
  });

  factory DailyTarget.fromJson(Map<String, dynamic> json) {
    return DailyTarget(
      calories: (json['calories'] ?? 0).toDouble(),
      proteinG: (json['protein_g'] ?? 0).toDouble(),
      carbsG: (json['carbs_g'] ?? 0).toDouble(),
      fatG: (json['fat_g'] ?? 0).toDouble(),
      fiberG: (json['fiber_g'] ?? 0).toDouble(),
      omega3G: (json['omega_3_g'] ?? 0).toDouble(),
      magnesiumMg: (json['magnesium_mg'] ?? 0).toDouble(),
      zincMg: (json['zinc_mg'] ?? 0).toDouble(),
      ironMg: (json['iron_mg'] ?? 0).toDouble(),
      calciumMg: (json['calcium_mg'] ?? 0).toDouble(),
      vitaminCMg: (json['vitamin_c_mg'] ?? 0).toDouble(),
      vitaminBComplexMg: (json['vitamin_b_complex_mg'] ?? 0).toDouble(),
      vitaminDMcg: (json['vitamin_d_mcg'] ?? 0).toDouble(),
      vitaminB12Mcg: (json['vitamin_b12_mcg'] ?? 0).toDouble(),
      vitaminAMcg: (json['vitamin_a_mcg'] ?? 0).toDouble(),
      folicAcidMcg: (json['folic_acid_mcg'] ?? 0).toDouble(),
    );
  }
}