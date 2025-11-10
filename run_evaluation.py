#!/usr/bin/env python3
"""
Avalia o modelo nos conjuntos 'valid' e 'test' dentro do dataset fornecido.
Gera: loss/accuracy (model.evaluate), classification_report, confusion_matrix, ROC AUC (se disponível).
"""
import os
import argparse
import numpy as np
from PIL import ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True

import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator

try:
    from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
    SKLEARN_AVAILABLE = True
except Exception:
    SKLEARN_AVAILABLE = False


def evaluate_set(model, generator, set_name):
    print(f"\n--- Avaliando {set_name} ---")
    steps = max(1, generator.samples // generator.batch_size)
    loss, *metrics = model.evaluate(generator, steps=steps, verbose=1)
    print(f"Resultado de model.evaluate (loss + metrics): { (loss, *metrics) }")

    # Previsões completas
    generator.reset()
    preds = model.predict(generator, verbose=0)
    # lidar com diferentes formatos de saída
    preds = np.ravel(preds)
    y_true = generator.classes[: len(preds)]

    # Converter para classes usando 0.5
    y_pred_labels = (preds > 0.5).astype(int)

    print("\nClassification report:")
    if SKLEARN_AVAILABLE:
        print(classification_report(y_true, y_pred_labels, target_names=list(generator.class_indices.keys())))
    else:
        # fallback simples
        acc = np.mean(y_true == y_pred_labels)
        print(f"Accuracy (fallback): {acc:.4f}")

    print("\nConfusion matrix:")
    if SKLEARN_AVAILABLE:
        print(confusion_matrix(y_true, y_pred_labels))
    else:
        cm = np.zeros((2,2), dtype=int)
        for a,b in zip(y_true, y_pred_labels):
            cm[a,b] += 1
        print(cm)

    if SKLEARN_AVAILABLE:
        # ROC AUC (se possível)
        try:
            auc = roc_auc_score(y_true, preds)
            print(f"\nROC AUC: {auc:.4f}")
        except Exception as e:
            print(f"\nROC AUC não calculada: {e}")

    # Estatísticas das probabilidades brutas e calibradas
    calibrated = np.where(preds > 0.5, preds, 1.0 - preds)
    print("\nEstatísticas das predições brutas:")
    print(f" min={np.min(preds):.6f}, max={np.max(preds):.6f}, mean={np.mean(preds):.6f}, std={np.std(preds):.6f}")
    print("Estatísticas da confiança calibrada:")
    print(f" min={np.min(calibrated):.2%}, max={np.max(calibrated):.2%}, mean={np.mean(calibrated):.2%}, std={np.std(calibrated):.2%}")

    low_conf = np.sum(calibrated < 0.55)
    print(f"Predições com confiança <55%: {low_conf}/{len(calibrated)}")

    return {
        'loss': float(loss),
        'preds': preds,
        'y_true': y_true,
        'y_pred_labels': y_pred_labels,
        'calibrated': calibrated,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', default='./models/latest.h5', help='Caminho para o modelo .h5')
    parser.add_argument('--dataset', default='./dataset', help='Pasta do dataset (contendo train/valid/test)')
    parser.add_argument('--batch-size', default=32, type=int)
    args = parser.parse_args()

    model_path = args.model
    if not os.path.exists(model_path):
        alt = './IdentyFIRE1.h5'
        if os.path.exists(alt):
            model_path = alt
            print(f"Modelo padrão não encontrado, usando {alt}")
        else:
            raise FileNotFoundError(f"Modelo não encontrado em {args.model} ou {alt}")

    if not os.path.isdir(args.dataset):
        raise FileNotFoundError(f"Dataset não encontrado em {args.dataset}")

    print(f"Carregando modelo de {model_path} ...")
    model = tf.keras.models.load_model(model_path)
    print("Modelo carregado com sucesso")

    # Data generators
    datagen = ImageDataGenerator(rescale=1.0/255)

    results = {}

    for split in ['valid', 'test']:
        split_dir = os.path.join(args.dataset, split)
        if not os.path.isdir(split_dir):
            print(f"Pasta {split} não encontrada em {args.dataset}, pulando")
            continue

        gen = datagen.flow_from_directory(
            directory=args.dataset,
            target_size=(150,150),
            batch_size=args.batch_size,
            classes=None,
            class_mode='binary',
            shuffle=False)
        # The generator above enumerates all subfolders; we want only the split
        # So create a generator pointing to that split specifically
        gen = datagen.flow_from_directory(
            directory=split_dir, target_size=(150,150), batch_size=args.batch_size, class_mode='binary', shuffle=False)

        res = evaluate_set(model, gen, split)
        results[split] = res

    print('\n' + '='*60)
    print('Avaliação concluída')

if __name__ == '__main__':
    main()
