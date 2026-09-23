import 'package:equatable/equatable.dart';

abstract class ProfileState extends Equatable {
  @override
  List<Object?> get props => [];
}

class ProfileInitial extends ProfileState {}

class ProfileChecking extends ProfileState {}

class ProfileLoaded extends ProfileState {
  final Map<String, dynamic> target;
  ProfileLoaded(this.target);

  @override
  List<Object?> get props => [target];
}

class ProfileMissing extends ProfileState {} 

class ProfileError extends ProfileState {
  final String message;
  ProfileError(this.message);

  @override
  List<Object?> get props => [message];
}