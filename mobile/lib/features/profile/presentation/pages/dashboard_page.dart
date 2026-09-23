import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../../auth/presentation/bloc/auth_bloc.dart';
import '../../../auth/presentation/bloc/auth_event.dart';
import '../../data/models/daily_target_model.dart';
import '../cubit/profile_cubit.dart';
import '../cubit/profile_state.dart';
import 'package:go_router/go_router.dart';

class DashboardPage extends StatelessWidget {
  const DashboardPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('NutriVision Pro - Dashboard'),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: () => context.read<AuthBloc>().add(SignOutRequested()),
          ),
        ],
      ),
      body: BlocBuilder<ProfileCubit, ProfileState>(
        builder: (context, state) {
          if (state is! ProfileLoaded) {
            return const Center(child: CircularProgressIndicator());
          }

          // Sesuaikan nama class dengan daily_target_model.dart kamu (DailyTargetModel / DailyTarget)
          final target = DailyTarget.fromJson(state.target);

          return ListView(
            padding: const EdgeInsets.all(16.0),
            children: [
              const Text(
                'Macronutrients',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              _NutrientCard('Calories', target.calories, 'kcal'),
              _NutrientCard('Protein', target.proteinG, 'g'),
              _NutrientCard('Carbohydrates', target.carbsG, 'g'),
              _NutrientCard('Fat', target.fatG, 'g'),
              _NutrientCard('Fiber', target.fiberG, 'g'),
              _NutrientCard('Omega-3', target.omega3G, 'g'),
              const SizedBox(height: 16),
              const Text(
                'Minerals',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              _NutrientCard('Magnesium', target.magnesiumMg, 'mg'),
              _NutrientCard('Zinc', target.zincMg, 'mg'),
              _NutrientCard('Iron', target.ironMg, 'mg'),
              _NutrientCard('Calcium', target.calciumMg, 'mg'),
              const SizedBox(height: 16),
              const Text(
                'Vitamins',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              _NutrientCard('Vitamin C', target.vitaminCMg, 'mg'),
              _NutrientCard(
                'Vitamin B Complex',
                target.vitaminBComplexMg,
                'mg',
              ),
              _NutrientCard('Vitamin D', target.vitaminDMcg, 'mcg'),
              _NutrientCard('Vitamin B12', target.vitaminB12Mcg, 'mcg'),
              _NutrientCard('Vitamin A', target.vitaminAMcg, 'mcg'),
              _NutrientCard('Folic Acid', target.folicAcidMcg, 'mcg'),
            ],
          );
        },
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () {
          print('--> SCAN BUTTON CLICKED');
          try {
            context.pushNamed('scan');
          } catch (e) {
            print('--> ERROR NAVIGATION: $e');
          }
        },
        icon: const Icon(Icons.camera_alt),
        label: const Text('Food Scan'),
        backgroundColor: Colors.green,
      ),
      floatingActionButtonLocation: FloatingActionButtonLocation.centerFloat,
    );
  }
}

class _NutrientCard extends StatelessWidget {
  final String label;
  final double value;
  final String unit;

  const _NutrientCard(this.label, this.value, this.unit);

  @override
  Widget build(BuildContext context) {
    return Card(
      child: ListTile(
        title: Text(label),
        trailing: Text(
          '${value.toStringAsFixed(1)} $unit',
          style: const TextStyle(fontWeight: FontWeight.bold),
        ),
      ),
    );
  }
}
