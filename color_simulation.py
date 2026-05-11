import numpy as np

# Simulate Protanopia (red weakness)
def protanopia_simulation(frame):
    matrix = np.array([
        [0.567, 0.433, 0],
        [0.558, 0.442, 0],
        [0,     0.242, 0.758]
    ])
    return apply_matrix(frame, matrix)


# Simulate Deuteranopia (green weakness)
def deuteranopia_simulation(frame):
    matrix = np.array([
        [0.625, 0.375, 0],
        [0.7,   0.3,   0],
        [0,     0.3,   0.7]
    ])
    return apply_matrix(frame, matrix)


def apply_matrix(frame, matrix):
    h, w, c = frame.shape
    reshaped = frame.reshape(-1, 3)

    transformed = np.dot(reshaped, matrix.T)
    transformed = np.clip(transformed, 0, 255)

    return transformed.reshape(h, w, 3).astype(np.uint8)