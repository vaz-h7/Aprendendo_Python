# \033(0:33:44m -> Dentro dos colchetes [estilo;cor da letra;cor de fundo]
'''
ESTILOS:
0 = Nada
1 = Negrito
4 = Sublinhado
7 = Inverte cor de texto com fundo

CORES DE LETRA:
30 = branco
31 = vermelho
32 = verde
33 = amarelo
34 = azul
35 = roxo
36 = ciano
37 = cinza

CORES DE FUNDO:
40 = branco
41 = vermelho
42 = verde
43 = amarelo
44 = azul
45 = roxo
46 = ciano
47 = cinza
'''

print('\033[1;30;46mTeste')
print('\033[7;30;46mTeste\033[m')
print('\033[4;31;30mTeste\033[m')
print('\033[;34;44mTeste\033[m')
print('\033[7;35;47mTeste\033[m')
#Teste