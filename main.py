from PIL import ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True

import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Dropout
from tensorflow.keras.preprocessing.image import ImageDataGenerator
import os
import numpy as np
import matplotlib.pyplot as plt

# Função de validação (opcional)
def validate_dataset(base_dir):
    from PIL import Image
    corrupted = []

    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                file_path = os.path.join(root, file)
                try:
                    with Image.open(file_path) as img:
                        img.verify()
                except Exception as e:
                    print(f"Corrompida: {file_path}")
                    corrupted.append(file_path)

    return corrupted

dataset_dir = 'C:\\Main\\Downloads\\archiveTI'

if os.path.exists(dataset_dir):
    # Validar dataset (opcional)
    print("Validando imagens...")
    corrupted = validate_dataset(dataset_dir)
    print(f"Imagens corrompidas encontradas: {len(corrupted)}")

    train_dir = os.path.join(dataset_dir, 'train')
    validation_dir = os.path.join(dataset_dir, 'valid')
    test_dir = os.path.join(dataset_dir, 'test')

    # Dimensões das imagens e tamanho do batch
    IMG_HEIGHT = 150
    IMG_WIDTH = 150
    BATCH_SIZE = 32

    # Criação de geradores de dados de imagem com data augmentation para o conjunto de treino
    train_image_generator = ImageDataGenerator(
        rescale=1./255,
        rotation_range=45,
        width_shift_range=.15,
        height_shift_range=.15,
        horizontal_flip=True,
        zoom_range=0.5
    )

    # Gerador de dados para validação e teste (apenas reescala)
    validation_image_generator = ImageDataGenerator(rescale=1./255)
    test_image_generator = ImageDataGenerator(rescale=1./255)

    # Carregamento dos dados de treino, validação e teste
    train_data_gen = train_image_generator.flow_from_directory(
        batch_size=BATCH_SIZE,
        directory=train_dir,
        shuffle=True,
        target_size=(IMG_HEIGHT, IMG_WIDTH),
        class_mode='binary'
    )

    val_data_gen = validation_image_generator.flow_from_directory(
        batch_size=BATCH_SIZE,
        directory=validation_dir,
        target_size=(IMG_HEIGHT, IMG_WIDTH),
        class_mode='binary'
    )

    test_data_gen = test_image_generator.flow_from_directory(
        batch_size=BATCH_SIZE,
        directory=test_dir,
        target_size=(IMG_HEIGHT, IMG_WIDTH),
        class_mode='binary',
        shuffle=False  # Importante: não embaralhar para manter ordem
    )

    # 2. Construção do Modelo (Rede Neural Convolucional)
    model = Sequential([
        Conv2D(32, (3, 3), activation='relu', input_shape=(IMG_HEIGHT, IMG_WIDTH, 3)),
        MaxPooling2D(2, 2),

        Conv2D(64, (3, 3), activation='relu'),
        MaxPooling2D(2, 2),

        Conv2D(128, (3, 3), activation='relu'),
        MaxPooling2D(2, 2),

        Conv2D(128, (3, 3), activation='relu'),
        MaxPooling2D(2, 2),

        Flatten(),
        Dropout(0.5),
        Dense(512, activation='relu'),
        Dense(1, activation='sigmoid')
    ])

    # 3. Compilação do Modelo
    model.compile(optimizer='adam',
                  loss='binary_crossentropy',
                  metrics=['accuracy'])

    model.summary()

    # 4. Treinamento do Modelo
    epochs = 25
    history = model.fit(
        train_data_gen,
        steps_per_epoch=train_data_gen.samples // BATCH_SIZE,
        epochs=epochs,
        validation_data=val_data_gen,
        validation_steps=val_data_gen.samples // BATCH_SIZE
    )

    # 5. Avaliação do Modelo
    acc = history.history['accuracy']
    val_acc = history.history['val_accuracy']

    loss = history.history['loss']
    val_loss = history.history['val_loss']

    epochs_range = range(epochs)

    plt.figure(figsize=(8, 8))
    plt.subplot(1, 2, 1)
    plt.plot(epochs_range, acc, label='Acurácia de Treino')
    plt.plot(epochs_range, val_acc, label='Acurácia de Validação')
    plt.legend(loc='lower right')
    plt.title('Acurácia de Treino e Validação')

    plt.subplot(1, 2, 2)
    plt.plot(epochs_range, loss, label='Perda de Treino')
    plt.plot(epochs_range, val_loss, label='Perda de Validação')
    plt.legend(loc='upper right')
    plt.title('Perda de Treino e Validação')
    plt.show()

    # Avaliação final com o conjunto de teste
    test_loss, test_acc = model.evaluate(test_data_gen, verbose=2)
    print('\nAcurácia no conjunto de teste:', test_acc)

    # 6. Predições em TOD0 o conjunto de teste
    print("\n=== Fazendo predições em todo o conjunto de teste ===")

    # Resetar o gerador de teste
    test_data_gen.reset()

    # Fazer predições em todas as imagens do conjunto de teste
    predictions = model.predict(test_data_gen, verbose=1)

    # Obter os rótulos verdadeiros
    true_labels = test_data_gen.classes

    # Converter predições para classes (0 ou 1)
    predicted_labels = (predictions > 0.5).astype(int).flatten()

    # Calcular métricas
    from sklearn.metrics import classification_report, confusion_matrix

    print("\n=== Relatório de Classificação ===")
    class_names = list(test_data_gen.class_indices.keys())
    print(classification_report(true_labels, predicted_labels, target_names=class_names))

    print("\n=== Matriz de Confusão ===")
    cm = confusion_matrix(true_labels, predicted_labels)
    print(cm)

    # Visualizar matriz de confusão
    plt.figure(figsize=(8, 6))
    plt.imshow(cm, interpolation='nearest', cmap=plt.cm.Blues)
    plt.title('Matriz de Confusão')
    plt.colorbar()
    tick_marks = np.arange(len(class_names))
    plt.xticks(tick_marks, class_names, rotation=45)
    plt.yticks(tick_marks, class_names)

    # Adicionar valores na matriz
    thresh = cm.max() / 2.
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            plt.text(j, i, format(cm[i, j], 'd'),
                     ha="center", va="center",
                     color="white" if cm[i, j] > thresh else "black")

    plt.ylabel('Rótulo Verdadeiro')
    plt.xlabel('Rótulo Predito')
    plt.tight_layout()
    plt.show()

    # Visualizar exemplos de predições (corretas e incorretas)
    print("\n=== Visualizando amostras de predições ===")

    # Coletar todas as imagens e informações
    test_data_gen.reset()
    all_images = []
    all_true_labels = []
    all_predictions = []

    for i in range(len(test_data_gen)):
        batch_images, batch_labels = test_data_gen[i]
        all_images.extend(batch_images)
        all_true_labels.extend(batch_labels)
        if i < len(predictions) // BATCH_SIZE:
            start_idx = i * BATCH_SIZE
            end_idx = min(start_idx + BATCH_SIZE, len(predictions))
            all_predictions.extend(predictions[start_idx:end_idx])

    # Selecionar algumas amostras aleatórias
    num_samples = min(16, len(all_images))
    sample_indices = np.random.choice(len(all_images), num_samples, replace=False)

    plt.figure(figsize=(16, 16))
    for i, idx in enumerate(sample_indices):
        plt.subplot(4, 4, i + 1)
        plt.imshow(all_images[idx])

        true_label = class_names[int(all_true_labels[idx])]
        pred_prob = all_predictions[idx][0]
        pred_label = class_names[1 if pred_prob > 0.5 else 0]

        # Cor do título: verde se correto, vermelho se incorreto
        color = 'green' if true_label == pred_label else 'red'

        plt.title(f'Real: {true_label}\nPred: {pred_label} ({pred_prob:.2%})',
                  color=color, fontsize=10)
        plt.axis('off')

    plt.tight_layout()
    plt.show()

    # Mostrar estatísticas gerais
    accuracy = np.mean(predicted_labels == true_labels)
    print(f"\n=== Estatísticas Gerais ===")
    print(f"Total de imagens testadas: {len(true_labels)}")
    print(f"Predições corretas: {np.sum(predicted_labels == true_labels)}")
    print(f"Predições incorretas: {np.sum(predicted_labels != true_labels)}")
    print(f"Acurácia: {accuracy:.2%}")

else:
    print(f"Diretório não encontrado: {dataset_dir}")
