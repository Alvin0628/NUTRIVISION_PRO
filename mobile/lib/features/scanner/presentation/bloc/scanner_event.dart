import 'dart:io';
import 'package:equatable/equatable.dart';

abstract class ScannerEvent extends Equatable {
  const ScannerEvent();

  @override
  List<Object?> get props => [];
}

class PickAndPredictImageEvent extends ScannerEvent {
  final File imageFile;

  const PickAndPredictImageEvent(this.imageFile);

  @override
  List<Object?> get props => [imageFile];
}

class ResetScannerEvent extends ScannerEvent {}