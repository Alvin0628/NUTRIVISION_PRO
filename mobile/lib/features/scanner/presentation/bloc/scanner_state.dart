import 'dart:io';
import 'package:equatable/equatable.dart';

abstract class ScannerState extends Equatable {
  const ScannerState();

  @override
  List<Object?> get props => [];
}

class ScannerInitial extends ScannerState {}

class ScannerLoading extends ScannerState {}

class ScannerSuccess extends ScannerState {
  final File imageFile;
  final Map<String, dynamic> predictionData;

  const ScannerSuccess({
    required this.imageFile,
    required this.predictionData,
  });

  @override
  List<Object?> get props => [imageFile, predictionData];
}

class ScannerFailure extends ScannerState {
  final String errorMessage;

  const ScannerFailure(this.errorMessage);

  @override
  List<Object?> get props => [errorMessage];
}