import numpy as np


A_G = np.array([
    #A, B, C, D, E, F, G, H, I, J
    [0, 1, 1, 0, 0, 0, 0, 0, 0, 0],#A
    [1, 0, 0, 1, 0, 0, 0, 0, 0, 0],#B
    [1, 0, 0, 0, 1, 0, 0, 0, 0, 0],#C
    [0, 1, 0, 0, 0, 1, 0, 0, 0, 0],#D
    [0, 0, 1, 0, 0, 1, 1, 0, 0, 0],#E
    [0, 0, 0, 1, 1, 0, 0, 1, 0, 0],#F
    [0, 0, 0, 0, 1, 0, 0, 0, 1, 0],#G
    [0, 0, 0, 0, 0, 1, 0, 0, 0, 1],#H
    [0, 0, 0, 0, 0, 0, 1, 0, 0, 1],#I
    [0, 0, 0, 0, 0, 0, 0, 1, 1, 0]#J
])

#eigenvecs and eigenvals
eigenvalues1, eigenvectors1 = np.linalg.eig(A_G)
print(eigenvalues1)



A_G_prime = np.array([
    #A, B, C, D, E, F, G, H, I, J
    [0, 1, 1, 0, 0, 0, 0, 0, 0, 0],#A
    [1, 0, 0, 1, 0, 0, 0, 0, 0, 0],#B
    [1, 0, 0, 0, 1, 0, 0, 0, 0, 0],#C
    [0, 1, 0, 0, 1, 0, 0, 0, 0, 0],#D
    [0, 0, 1, 1, 0, 1, 0, 0, 0, 0],#E
    [0, 0, 0, 0, 1, 0, 1, 1, 0, 0],#F
    [0, 0, 0, 0, 0, 1, 0, 0, 1, 0],#G
    [0, 0, 0, 0, 0, 1, 0, 0, 0, 1],#H
    [0, 0, 0, 0, 0, 0, 1, 0, 0, 1],#I
    [0, 0, 0, 0, 0, 0, 0, 1, 1, 0]#J
])

eigenvalues2, eigenvectors2 = np.linalg.eig(A_G_prime)
print("second eigen")
print(eigenvalues2)
#print columns of eigenvectors2


#ones vector
ones = np.ones(len(A_G))

print(np.dot(eigenvectors1[:, 7], ones))
print(np.dot(eigenvectors2[:, 8], ones))

for col in range(len(eigenvectors1[0])):
    print(np.dot(eigenvectors2[:, col], ones))