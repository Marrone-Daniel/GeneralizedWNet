python PipelineScripts.py --decoder EncoderCvCvCvCv  --mixer MixerMaxRes7@3  --encoder DecoderVit@2@24Vit@2@12CvCv --batchSize 12 --initLr 0.001 --epochs 81 --resumeTrain 0 --config PF64-PF50-1GPU-NewAug
python PipelineScripts.py --decoder EncoderCbbCbbCbbCbb  --mixer MixerMaxRes7@3  --encoder DecoderVit@2@24Vit@2@12CbbCbb  --batchSize 12 --initLr 0.001 --epochs 81 --resumeTrain 0 --config PF64-PF50-1GPU-NewAug
python PipelineScripts.py --decoder EncoderCbnCbnCbnCbn  --mixer MixerMaxRes7@3  --encoder DecoderVit@2@24Vit@2@12CbnCbn  --batchSize 12 --initLr 0.001 --epochs 81 --resumeTrain 0 --config PF64-PF50-1GPU-NewAug