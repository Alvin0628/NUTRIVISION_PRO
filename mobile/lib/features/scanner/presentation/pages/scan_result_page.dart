import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

class ScanResultPage extends StatefulWidget {
  final File imageFile;
  final Map<String, dynamic> initialPredictionResult;
  final String baseUrl;

  const ScanResultPage({
    super.key,
    required this.imageFile,
    required this.initialPredictionResult,
    required this.baseUrl,
  });

  @override
  State<ScanResultPage> createState() => _ScanResultPageState();
}

class _ScanResultPageState extends State<ScanResultPage> {
  late String _imageId;
  List<dynamic> _detectedClasses = [];
  List<dynamic> _nutrients = [];
  Map<String, dynamic> _totals = {};

  final Map<String, double> _gramsMap = {};
  Timer? _debounce; // Prevents request spamming while adjusting the slider
  bool _isSaving = false;

  @override
  void initState() {
    super.initState();
    _parseData(widget.initialPredictionResult);
  }

  void _parseData(Map<String, dynamic> data) {
    setState(() {
      _imageId = data['image_id'] ?? '';
      _detectedClasses = data['detected_classes'] ?? [];
      _nutrients = data['nutrients'] ?? [];
      _totals = data['totals'] ?? {};

      for (var item in _detectedClasses) {
        final className = item['class_name'].toString();
        final grams = (item['estimated_grams'] as num?)?.toDouble() ?? 100.0;
        if (!_gramsMap.containsKey(className)) {
          _gramsMap[className] = grams;
        }
      }
    });
  }

  // Background sync with Optimistic UI (no intrusive loading screen)
  void _onSliderChanged(String className, double val) {
    setState(() {
      _gramsMap[className] = val;
    });

    if (_debounce?.isActive ?? false) _debounce!.cancel();
    _debounce = Timer(const Duration(milliseconds: 500), () {
      _updateGramsOnBackend();
    });
  }

  Future<void> _updateGramsOnBackend() async {
    try {
      final response = await http.post(
        Uri.parse('${widget.baseUrl}/recalculate'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          "image_id": _imageId,
          "grams_map": _gramsMap,
          "serving_style_map": {},
        }),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        _parseData(data);
      }
    } catch (e) {
      print("Background sync error: $e");
    }
  }

  // Remove component by class_name so the card completely disappears from UI
  Future<void> _removeComponentCompletely(String className) async {
    final itemToRemove = _detectedClasses.firstWhere(
      (item) => item['class_name'].toString() == className,
      orElse: () => null,
    );

    if (itemToRemove == null) return;

    try {
      await http.post(
        Uri.parse('${widget.baseUrl}/feedback/remove'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          "image_id": _imageId,
          "detection_id": itemToRemove['detection_id'] ?? '',
          "original_class": className,
          "mask_polygon": itemToRemove['mask_polygon'] ?? [],
        }),
      );

      setState(() {
        _detectedClasses.removeWhere(
          (item) => item['class_name'].toString() == className,
        );
        _gramsMap.remove(className);
      });

      await _updateGramsOnBackend();
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Component $className successfully removed.')),
      );
    } catch (e) {
      print("Removal error: $e");
    }
  }

  void _showAddFoodDialog() {
    final TextEditingController controller = TextEditingController();
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Add Food (False Negative)'),
        content: TextField(
          controller: controller,
          decoration: const InputDecoration(
            hintText: 'Food Name (e.g., sambal, tofu)',
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () async {
              Navigator.pop(context);
              if (controller.text.isNotEmpty) {
                await _submitMissingFood(controller.text.trim());
              }
            },
            child: const Text('Add'),
          ),
        ],
      ),
    );
  }

  Future<void> _submitMissingFood(String foodName) async {
    try {
      final response = await http.post(
        Uri.parse('${widget.baseUrl}/feedback/missing'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          "image_id": _imageId,
          "food_name": foodName,
          "tap_x": 0.5,
          "tap_y": 0.5,
        }),
      );

      if (response.statusCode == 200) {
        setState(() {
          final normalizedName = foodName.toLowerCase();
          _gramsMap[normalizedName] = 100.0;
          _detectedClasses.add({
            "detection_id": "manual_${DateTime.now().millisecondsSinceEpoch}",
            "class_name": normalizedName,
            "confidence": 1.0,
            "bbox": [0, 0, 100, 100],
            "mask_polygon": [],
            "estimated_grams": 100.0,
          });
        });
        await _updateGramsOnBackend();
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Food $foodName successfully added!')),
        );
      }
    } catch (e) {
      print("Missing food error: $e");
    }
  }

  // Function to save/log food to daily diary
  Future<void> _saveToDiary() async {
    setState(() {
      _isSaving = true;
    });

    try {
      final response = await http.post(
        Uri.parse('${widget.baseUrl}/log'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({"image_id": _imageId}),
      );

      if (response.statusCode == 200) {
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Successfully saved to nutrition diary!'),
          ),
        );
        // Return to previous page / home after successful save
        Navigator.pop(context, true);
      } else {
        throw Exception('Failed to save to server');
      }
    } catch (e) {
      print("Saving log error: $e");
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('An error occurred while saving.')),
      );
    } finally {
      setState(() {
        _isSaving = false;
      });
    }
  }

  // Display Modal containing all 16 Nutrients
  void _showAllNutrientsModal(String title, Map<String, dynamic> nutrientMap) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) => DraggableScrollableSheet(
        initialChildSize: 0.6,
        minChildSize: 0.4,
        maxChildSize: 0.85,
        expand: false,
        builder: (context, scrollController) => Padding(
          padding: const EdgeInsets.all(20.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                '16 Nutrients Breakdown: ${title.toUpperCase()}',
                style: const TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const Divider(),
              Expanded(
                child: ListView(
                  controller: scrollController,
                  children: nutrientMap.entries.map((entry) {
                    return ListTile(
                      dense: true,
                      title: Text(
                        entry.key.replaceAll('_', ' ').toUpperCase(),
                        style: const TextStyle(
                          fontSize: 13,
                          color: Colors.grey,
                        ),
                      ),
                      trailing: Text(
                        '${entry.value}',
                        style: const TextStyle(
                          fontSize: 14,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    );
                  }).toList(),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  @override
  void dispose() {
    _debounce?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final Map<String, dynamic> uniqueGroupedItems = {};
    for (var item in _detectedClasses) {
      final name = item['class_name'].toString();
      if (!uniqueGroupedItems.containsKey(name)) {
        uniqueGroupedItems[name] = item;
      }
    }

    final totalCalories = _totals['total_calories'] ?? 0.0;
    final totalProtein = _totals['total_protein_g'] ?? 0.0;
    final totalCarbs = _totals['total_carbs_g'] ?? 0.0;
    final totalFat = _totals['total_fat_g'] ?? 0.0;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Scan Result & Nutrition'),
        centerTitle: true,
        actions: [
          IconButton(
            icon: const Icon(Icons.add_circle_outline),
            tooltip: 'Add New Food',
            onPressed: _showAddFoodDialog,
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            ClipRRect(
              borderRadius: BorderRadius.circular(16),
              child: Image.file(
                widget.imageFile,
                width: double.infinity,
                height: 200,
                fit: BoxFit.cover,
              ),
            ),
            const SizedBox(height: 16),

            // Total Aggregation Card + View All 16 Nutrients Button
            Card(
              elevation: 3,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(16),
              ),
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text(
                          'Total Estimated Calories',
                          style: TextStyle(
                            fontWeight: FontWeight.bold,
                            fontSize: 16,
                          ),
                        ),
                        Text(
                          '$totalCalories kcal',
                          style: const TextStyle(
                            fontSize: 20,
                            fontWeight: FontWeight.bold,
                            color: Colors.green,
                          ),
                        ),
                      ],
                    ),
                    const Divider(height: 24),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceAround,
                      children: [
                        _buildNutrientStat(
                          'Protein',
                          '${totalProtein}g',
                          Colors.blue,
                        ),
                        _buildNutrientStat(
                          'Carbs',
                          '${totalCarbs}g',
                          Colors.orange,
                        ),
                        _buildNutrientStat(
                          'Fat',
                          '${totalFat}g',
                          Colors.redAccent,
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    Center(
                      child: TextButton.icon(
                        onPressed: () =>
                            _showAllNutrientsModal('Overall Total', _totals),
                        icon: const Icon(Icons.list_alt, size: 18),
                        label: const Text('View All 16 Nutrient Components'),
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 20),

            const Text(
              'Detected Components (Grouped)',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 10),

            ListView.builder(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              itemCount: uniqueGroupedItems.keys.length,
              itemBuilder: (context, index) {
                final className = uniqueGroupedItems.keys.elementAt(index);
                final currentGrams = _gramsMap[className] ?? 100.0;

                final nutrientData = _nutrients.firstWhere(
                  (n) =>
                      n['class_name'].toString().toLowerCase() ==
                      className.toLowerCase(),
                  orElse: () => {},
                );

                final cal = nutrientData['calories'] ?? 0.0;
                final protein = nutrientData['protein_g'] ?? 0.0;
                final carbs = nutrientData['carbs_g'] ?? 0.0;
                final fat = nutrientData['fat_g'] ?? 0.0;
                final fiber = nutrientData['fiber_g'] ?? 0.0;

                return Card(
                  margin: const EdgeInsets.only(bottom: 12),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Padding(
                    padding: const EdgeInsets.all(12.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Text(
                              className.toUpperCase(),
                              style: const TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                            IconButton(
                              icon: const Icon(
                                Icons.delete_outline,
                                color: Colors.red,
                                size: 20,
                              ),
                              tooltip: 'Remove Component',
                              onPressed: () =>
                                  _removeComponentCompletely(className),
                            ),
                          ],
                        ),
                        const SizedBox(height: 4),
                        Text(
                          'Portion: ${currentGrams.toStringAsFixed(0)} grams',
                          style: const TextStyle(
                            color: Colors.grey,
                            fontSize: 13,
                          ),
                        ),

                        // Slider with Optimistic UI
                        Slider(
                          value: currentGrams,
                          min: 10.0,
                          max: 500.0,
                          divisions: 49,
                          label: '${currentGrams.round()}g',
                          onChanged: (val) => _onSliderChanged(className, val),
                        ),

                        const Divider(),
                        Wrap(
                          spacing: 12,
                          runSpacing: 4,
                          children: [
                            Text(
                              'Cal: $cal kcal',
                              style: const TextStyle(
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                            Text('P: ${protein}g'),
                            Text('C: ${carbs}g'),
                            Text('F: ${fat}g'),
                            Text(
                              'Fiber: ${fiber}g',
                              style: const TextStyle(color: Colors.grey),
                            ),
                          ],
                        ),
                        const SizedBox(height: 4),
                        Align(
                          alignment: Alignment.centerRight,
                          child: TextButton(
                            style: TextButton.styleFrom(
                              padding: EdgeInsets.zero,
                              minimumSize: const Size(50, 30),
                            ),
                            onPressed: () =>
                                _showAllNutrientsModal(className, nutrientData),
                            child: const Text(
                              '16 Nutrients Detail >',
                              style: TextStyle(fontSize: 12),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                );
              },
            ),
            const SizedBox(height: 24),

            // Final Submit / Save to Diary Button
            SizedBox(
              width: double.infinity,
              height: 50,
              child: ElevatedButton(
                onPressed: _isSaving ? null : _saveToDiary,
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.green,
                  foregroundColor: Colors.white,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
                child: _isSaving
                    ? const SizedBox(
                        width: 24,
                        height: 24,
                        child: CircularProgressIndicator(
                          color: Colors.white,
                          strokeWidth: 2,
                        ),
                      )
                    : const Text(
                        'Save to Nutrition Diary',
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
              ),
            ),
            const SizedBox(height: 20),
          ],
        ),
      ),
    );
  }

  Widget _buildNutrientStat(String title, String value, Color color) {
    return Column(
      children: [
        Text(title, style: const TextStyle(fontSize: 12, color: Colors.grey)),
        const SizedBox(height: 4),
        Text(
          value,
          style: TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.bold,
            color: color,
          ),
        ),
      ],
    );
  }
}
