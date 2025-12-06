from PIL import ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True

import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Dropout
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau, ModelCheckpoint
import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import time
import json

# ACEITAR ARGUMENTOS DA LINHA DE COMANDO
if len(sys.argv) > 1:
    dataset_dir = sys.argv[1]
    model_name = sys.argv[2] if len(sys.argv) > 2 else "IdentyFIRE_model"
    epochs = int(sys.argv[3]) if len(sys.argv) > 3 else 25
    BATCH_SIZE = int(sys.argv[4]) if len(sys.argv) > 4 else 32
else:
    dataset_dir = "C:/Dataset/archive"
    model_name = "IdentyFIRE_model"
    epochs = 25
    BATCH_SIZE = 32

# CONFIGURAÇÃO PARA DirectML
print("=" * 60)
print("CONFIGURAÇÃO DA GPU (DirectML)")
print("=" * 60)

# Forçar uso do DirectML
os.environ['TF_DIRECTML_PATH'] = ''  # Garante que o TensorFlow-DirectML seja usado

gpus = tf.config.list_physical_devices("GPU")
if gpus:
    try:
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)

        logical_gpus = tf.config.list_logical_devices("GPU")
        print(f"✓ {len(gpus)} GPU(s) detectada(s)")
        print(f"✓ Usando DirectML (funciona com AMD, Intel, NVIDIA)")

    except RuntimeError as e:
        print(f"⚠ Erro: {e}")
else:
    print("⚠ GPU não detectada - usando CPU")

print("=" * 60 + "\n")


# FUNÇÃO DE VALIDAÇÃO (Usar caso de erro)
def validate_dataset(base_dir):
    from PIL import Image
    corrupted = []

    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.lower().endswith((".png", ".jpg", ".jpeg")):
                file_path = os.path.join(root, file)
                try:
                    with Image.open(file_path) as img:
                        img.verify()
                except Exception as e:
                    print(f"Corrompida: {file_path}")
                    corrupted.append(file_path)

    return corrupted


# CONFIGURAÇÃO DO DATASET
if os.path.exists(dataset_dir):
    start_time = time.time()

    corrupted = []

    train_dir = os.path.join(dataset_dir, "train")
    validation_dir = os.path.join(dataset_dir, "valid")
    test_dir = os.path.join(dataset_dir, "test")

    # PARÂMETROS
    IMG_HEIGHT = 150
    IMG_WIDTH = 150
    NUM_WORKERS = 4

    # GERADORES DE DADOS
    train_image_generator = ImageDataGenerator(
        rescale=1.0 / 255,
        rotation_range=45,
        width_shift_range=0.15,
        height_shift_range=0.15,
        horizontal_flip=True,
        zoom_range=0.5,
        fill_mode='nearest'
    )

    validation_image_generator = ImageDataGenerator(rescale=1.0 / 255)
    test_image_generator = ImageDataGenerator(rescale=1.0 / 255)

    train_data_gen = train_image_generator.flow_from_directory(
        batch_size=BATCH_SIZE,
        directory=train_dir,
        shuffle=True,
        target_size=(IMG_HEIGHT, IMG_WIDTH),
        class_mode="binary",
    )

    val_data_gen = validation_image_generator.flow_from_directory(
        batch_size=BATCH_SIZE,
        directory=validation_dir,
        target_size=(IMG_HEIGHT, IMG_WIDTH),
        class_mode="binary",
    )

    test_data_gen = test_image_generator.flow_from_directory(
        batch_size=BATCH_SIZE,
        directory=test_dir,
        target_size=(IMG_HEIGHT, IMG_WIDTH),
        class_mode="binary",
        shuffle=False,
    )

    print(f"✓ Dataset carregado:")
    print(f"  - Treino: {train_data_gen.samples} imagens")
    print(f"  - Validação: {val_data_gen.samples} imagens")
    print(f"  - Teste: {test_data_gen.samples} imagens")
    print(f"  - Batch size: {BATCH_SIZE}")
    print(f"  - Épocas: {epochs}\n")

    # MODELO
    model = Sequential([
        Conv2D(32, (3, 3), activation="relu", padding='same',
               input_shape=(IMG_HEIGHT, IMG_WIDTH, 3)),
        MaxPooling2D(2, 2),

        Conv2D(64, (3, 3), activation="relu", padding='same'),
        MaxPooling2D(2, 2),

        Conv2D(128, (3, 3), activation="relu", padding='same'),
        MaxPooling2D(2, 2),

        Conv2D(128, (3, 3), activation="relu", padding='same'),
        MaxPooling2D(2, 2),

        Flatten(),
        Dropout(0.5),
        Dense(512, activation="relu"),
        Dense(1, activation="sigmoid"),
    ])

    # COMPILAÇÃO
    optimizer = tf.keras.optimizers.Adam(learning_rate=0.001)

    model.compile(
        optimizer=optimizer,
        loss="binary_crossentropy",
        metrics=["accuracy"]
    )

    model.summary()

    # CALLBACKS
    callbacks = [
        EarlyStopping(
            monitor='val_loss',
            patience=5,
            restore_best_weights=True,
            verbose=1
        ),

        ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.5,
            patience=3,
            min_lr=1e-7,
            verbose=1
        ),

        ModelCheckpoint(
            f'{model_name}_best.h5',
            monitor='val_accuracy',
            save_best_only=True,
            verbose=1
        )
    ]

    # TREINAMENTO
    print("\n" + "=" * 60)
    print("INICIANDO TREINAMENTO")
    print("=" * 60 + "\n")

    steps_per_epoch = max(1, train_data_gen.samples // BATCH_SIZE)
    validation_steps = max(1, val_data_gen.samples // BATCH_SIZE)

    history = model.fit(
        train_data_gen,
        steps_per_epoch=steps_per_epoch,
        epochs=epochs,
        validation_data=val_data_gen,
        validation_steps=validation_steps,
        callbacks=callbacks,
        workers=NUM_WORKERS,
        use_multiprocessing=False,
        verbose=1
    )

    print("\n" + "=" * 60)
    print("TREINAMENTO CONCLUÍDO")
    print("=" * 60 + "\n")

    # AVALIAÇÃO
    acc = history.history["accuracy"]
    val_acc = history.history["val_accuracy"]
    loss = history.history["loss"]
    val_loss = history.history["val_loss"]

    epochs_range = range(len(acc))

    plt.figure(figsize=(12, 5))

    plt.subplot(1, 2, 1)
    plt.plot(epochs_range, acc, label="Acurácia de Treino", linewidth=2)
    plt.plot(epochs_range, val_acc, label="Acurácia de Validação", linewidth=2)
    plt.legend(loc="lower right")
    plt.title("Acurácia de Treino e Validação")
    plt.xlabel("Época")
    plt.ylabel("Acurácia")
    plt.grid(True, alpha=0.3)

    plt.subplot(1, 2, 2)
    plt.plot(epochs_range, loss, label="Perda de Treino", linewidth=2)
    plt.plot(epochs_range, val_loss, label="Perda de Validação", linewidth=2)
    plt.legend(loc="upper right")
    plt.title("Perda de Treino e Validação")
    plt.xlabel("Época")
    plt.ylabel("Perda")
    plt.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(f'{model_name}_training_history.png', dpi=300, bbox_inches='tight')
    print(f"✓ Gráfico salvo: {model_name}_training_history.png")

    # TESTE
    print("\n=== Avaliação no Conjunto de Teste ===")
    test_loss, test_acc = model.evaluate(test_data_gen, verbose=2)
    print(f"\n✓ Acurácia de Teste: {test_acc:.4f} ({test_acc * 100:.2f}%)")

    # PREDIÇÕES
    print("\n=== Fazendo Predições ===")
    test_data_gen.reset()

    predictions = model.predict(test_data_gen, verbose=1)
    true_labels = test_data_gen.classes
    predicted_labels = (predictions > 0.5).astype(int).flatten()

    from sklearn.metrics import classification_report, confusion_matrix

    print("\n=== Relatório de Classificação ===")
    class_names = list(test_data_gen.class_indices.keys())
    print(classification_report(true_labels, predicted_labels, target_names=class_names))

    print("\n=== Matriz de Confusão ===")
    cm = confusion_matrix(true_labels, predicted_labels)
    print(cm)

    plt.figure(figsize=(8, 6))
    plt.imshow(cm, interpolation="nearest", cmap=plt.cm.Blues)
    plt.title("Matriz de Confusão", fontsize=14, fontweight='bold')
    plt.colorbar()
    tick_marks = np.arange(len(class_names))
    plt.xticks(tick_marks, class_names, rotation=45)
    plt.yticks(tick_marks, class_names)

    thresh = cm.max() / 2.0
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            plt.text(
                j, i, format(cm[i, j], "d"),
                ha="center", va="center",
                color="white" if cm[i, j] > thresh else "black",
                fontsize=12, fontweight='bold'
            )

    plt.ylabel("Rótulo Verdadeiro")
    plt.xlabel("Rótulo Predito")
    plt.tight_layout()
    plt.savefig(f'{model_name}_confusion_matrix.png', dpi=300, bbox_inches='tight')
    print(f"✓ Matriz de confusão salva: {model_name}_confusion_matrix.png")

    # SALVAR MODELO
    model.save(f"{model_name}.h5")
    print(f"\n✓ Modelo salvo: {model_name}.h5")

    end_time = time.time()
    execution_time = end_time - start_time
    minutes = execution_time // 60
    seconds = execution_time % 60

    # SALVAR RESULTADOS EM JSON
    results = {
        "model_name": model_name,
        "test_accuracy": float(test_acc),
        "test_loss": float(test_loss),
        "training_time": f"{int(minutes)}min {seconds:.2f}s",
        "epochs_trained": len(acc),
        "batch_size": BATCH_SIZE,
        "dataset_dir": dataset_dir
    }

    with open(f'{model_name}_results.json', 'w') as f:
        json.dump(results, f, indent=4)

    print(f"\n{'=' * 60}")
    print(f"Tempo total: {int(minutes)}min {seconds:.2f}s")
    print(f"{'=' * 60}\n")

else:
    print(f"⚠ Diretório não encontrado: {dataset_dir}")
    sys.exit(1)
