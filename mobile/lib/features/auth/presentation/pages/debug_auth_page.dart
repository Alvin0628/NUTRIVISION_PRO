import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../../../core/network/api_client.dart';
import '../bloc/auth_bloc.dart';
import '../bloc/auth_event.dart';
import '../bloc/auth_state.dart';

class DebugAuthPage extends StatefulWidget {
  const DebugAuthPage({super.key});

  @override
  State<DebugAuthPage> createState() => _DebugAuthPageState();
}

class _DebugAuthPageState extends State<DebugAuthPage> {
  final _emailController = TextEditingController(text: 'testuser@nutrivision.com');
  final _passwordController = TextEditingController(text: 'password123');
  String _apiResponse = 'No API calls yet.';

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('NutriVision - Auth & Network Debug')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            BlocBuilder<AuthBloc, AuthState>(
              builder: (context, state) {
                return Container(
                  padding: const EdgeInsets.all(12),
                  color: Colors.grey[200],
                  child: Text(
                    'Current State: ${state.runtimeType}\nDetails: $state',
                    style: const TextStyle(fontWeight: FontWeight.bold),
                  ),
                );
              },
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _emailController,
              decoration: const InputDecoration(labelText: 'Email'),
            ),
            TextField(
              controller: _passwordController,
              decoration: const InputDecoration(labelText: 'Password'),
              obscureText: true,
            ),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: () {
                context.read<AuthBloc>().add(
                      SignUpRequested(
                        email: _emailController.text,
                        password: _passwordController.text,
                      ),
                    );
              },
              child: const Text('Register new Email'),
            ),
            ElevatedButton(
              onPressed: () {
                context.read<AuthBloc>().add(
                      SignInRequested(
                        email: _emailController.text,
                        password: _passwordController.text,
                      ),
                    );
              },
              child: const Text('Login Email'),
            ),
            ElevatedButton(
              onPressed: () {
                context.read<AuthBloc>().add(GoogleSignInRequested());
              },
              child: const Text('Login via Google'),
            ),
            ElevatedButton(
              onPressed: () {
                context.read<AuthBloc>().add(SignOutRequested());
              },
              style: ElevatedButton.styleFrom(backgroundColor: Colors.red[100]),
              child: const Text('Sign Out'),
            ),
            const Divider(height: 32),
            ElevatedButton(
              onPressed: () async {
                setState(() => _apiResponse = 'Call backend...');
                try {
                  final client = ApiClient();
                  final res = await client.dio.get('/users/target');
                  setState(() => _apiResponse = 'SUCCESS (Response Data):\n${res.data}');
                } catch (e) {
                  setState(() => _apiResponse = 'RESPONSE ERROR/HTTP:\n$e');
                }
              },
              style: ElevatedButton.styleFrom(backgroundColor: Colors.green[100]),
              child: const Text('Test Authenticated Call (/users/target)'),
            ),
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.all(12),
              color: Colors.black12,
              child: Text(
                _apiResponse,
                style: const TextStyle(fontFamily: 'monospace', fontSize: 12),
              ),
            ),
          ],
        ),
      ),
    );
  }
}