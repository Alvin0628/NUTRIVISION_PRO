import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../../auth/presentation/bloc/auth_bloc.dart';
import '../../../auth/presentation/bloc/auth_event.dart'; // Import AuthEvent
import '../../../auth/presentation/bloc/auth_state.dart';
import '../cubit/profile_cubit.dart';
import '../cubit/profile_state.dart';

class OnboardingPage extends StatefulWidget {
  const OnboardingPage({super.key});

  @override
  State<OnboardingPage> createState() => _OnboardingPageState();
}

class _OnboardingPageState extends State<OnboardingPage> {
  final _ageController = TextEditingController(text: '25');
  final _heightController = TextEditingController(text: '170');
  final _weightController = TextEditingController(text: '65');
  String _gender = 'male';
  String _activityLevel = 'moderate';
  String _goal = 'maintenance';

  @override
  void dispose() {
    _ageController.dispose();
    _heightController.dispose();
    _weightController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final authState = context.watch<AuthBloc>().state;
    final uid = authState is Authenticated ? authState.uid : '';

    return Scaffold(
      appBar: AppBar(
        title: const Text('Complete Your Profile'),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            tooltip: 'Logout',
            onPressed: () {
              // Trigger event SignOut agar router me-redirect ke /login
              context.read<AuthBloc>().add(SignOutRequested());
            },
          ),
        ],
      ),
      body: BlocConsumer<ProfileCubit, ProfileState>(
        listener: (context, state) {
          if (state is ProfileError) {
            ScaffoldMessenger.of(
              context,
            ).showSnackBar(SnackBar(content: Text(state.message)));
          }
        },
        builder: (context, state) {
          if (state is ProfileChecking) {
            return const Center(child: CircularProgressIndicator());
          }

          return SingleChildScrollView(
            padding: const EdgeInsets.all(16.0),
            child: Column(
              children: [
                const Text(
                  'Enter your personal details below to calculate your daily nutritional targets.',
                  style: TextStyle(fontSize: 16),
                ),
                const SizedBox(height: 20),
                TextField(
                  controller: _ageController,
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(labelText: 'Age (year)'),
                ),
                TextField(
                  controller: _heightController,
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(labelText: 'Height (cm)'),
                ),
                TextField(
                  controller: _weightController,
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(labelText: 'Weight (kg)'),
                ),
                const SizedBox(height: 10),
                DropdownButtonFormField<String>(
                  value: _gender,
                  decoration: const InputDecoration(labelText: 'Gender'),
                  items: const [
                    DropdownMenuItem(value: 'male', child: Text('Male')),
                    DropdownMenuItem(value: 'female', child: Text('Female')),
                  ],
                  onChanged: (val) => setState(() => _gender = val!),
                ),
                DropdownButtonFormField<String>(
                  value: _activityLevel,
                  decoration: const InputDecoration(
                    labelText: 'Activity Level',
                  ),
                  items: const [
                    DropdownMenuItem(
                      value: 'sedentary',
                      child: Text('Sedentary (Rarely exercises)'),
                    ),
                    DropdownMenuItem(
                      value: 'light',
                      child: Text('Light (1-3 day/week)'),
                    ),
                    DropdownMenuItem(
                      value: 'moderate',
                      child: Text('Moderate (3-5 day/week)'),
                    ),
                    DropdownMenuItem(
                      value: 'active',
                      child: Text('Active (6-7 day/week)'),
                    ),
                  ],
                  onChanged: (val) => setState(() => _activityLevel = val!),
                ),
                DropdownButtonFormField<String>(
                  value: _goal,
                  decoration: const InputDecoration(
                    labelText: 'Nutrition Target',
                  ),
                  items: const [
                    DropdownMenuItem(
                      value: 'cutting',
                      child: Text('Lose weight'),
                    ),
                    DropdownMenuItem(
                      value: 'maintenance',
                      child: Text('Maintain weight'),
                    ),
                    DropdownMenuItem(
                      value: 'bulking',
                      child: Text('Gaining Weight'),
                    ),
                  ],
                  onChanged: (val) => setState(() => _goal = val!),
                ),
                const SizedBox(height: 30),
                ElevatedButton(
                  onPressed: () {
                    context.read<ProfileCubit>().submitOnboarding({
                      'uid': uid,
                      'gender': _gender,
                      'age': int.parse(_ageController.text),
                      'height_cm': double.parse(_heightController.text),
                      'weight_kg': double.parse(_weightController.text),
                      'activity_level': _activityLevel,
                      'goal': _goal,
                    });
                  },
                  child: const Text('Save & Access Dashboard'),
                ),
              ],
            ),
          );
        },
      ),
    );
  }
}
