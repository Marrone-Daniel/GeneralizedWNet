python PipelineScripts.py --encoder EncoderCvCvVit@2@12Vit@2@24  --mixer MixerMaxRes7@3  --batchSize 12 --initLr 0.001 --epochs 81 --resumeTrain 0 --config PF64-PF50-2GPUs-OldAug
python PipelineScripts.py --encoder EncoderCbbCbbVit@2@12Vit@2@24  --mixer MixerMaxRes7@3  --batchSize 12 --initLr 0.001 --epochs 81 --resumeTrain 0 --config PF64-PF50-2GPUs-OldAug
python PipelineScripts.py --encoder EncoderCbnCbnVit@2@12Vit@2@24  --mixer MixerMaxRes7@3  --batchSize 12 --initLr 0.001 --epochs 81 --resumeTrain 0 --config PF64-PF50-2GPUs-OldAug