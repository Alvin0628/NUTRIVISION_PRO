import 'package:flutter_bloc/flutter_bloc.dart';
import '../../data/scanner_repository.dart';
import 'scanner_event.dart';
import 'scanner_state.dart';

class ScannerBloc extends Bloc<ScannerEvent, ScannerState> {
  final ScannerRepository repository;

  ScannerBloc({required this.repository}) : super(ScannerInitial()) {
    on<PickAndPredictImageEvent>(_onPickAndPredictImage);
    on<ResetScannerEvent>((event, emit) => emit(ScannerInitial()));
  }

  Future<void> _onPickAndPredictImage(
    PickAndPredictImageEvent event,
    Emitter<ScannerState> emit,
  ) async {
    emit(ScannerLoading());
    try {
      final result = await repository.predictFoodImage(event.imageFile);
      emit(ScannerSuccess(
        imageFile: event.imageFile,
        predictionData: result,
      ));
    } catch (e) {
      emit(ScannerFailure(e.toString()));
    }
  }
}