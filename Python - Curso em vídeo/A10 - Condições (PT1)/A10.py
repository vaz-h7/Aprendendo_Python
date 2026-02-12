'''
Caminhos que o carro pode seguir na estrada para chegar ao destino:
Esquerda ou direita, se seguir pela direita vai respeitar uma série de comandos (esquerda), senão, vai pela direita e seguir outra série de comandos (direita).
Se e senão (if and else)
Exemplo:
se carro.esquerda() bloco verdadeiro
se carro.direita() bloco falso
if carro.esquerda() bloco True
else bloco False
'''


tempo = int(input('Quantos anos tem seu carro? '))
'''if tempo <= 3:
    print('Seu carro é novo!')
else:
    print('Que lata velha!')'''
print('Seu carro é novo!' if tempo<=3 else 'Que lata velha!')
print('FIM')

nome = str(input('Qual seu nome? '))
if nome == 'João':
    print('Que nome bonito!')
print(f'Bom dia, {nome}!')

n1 = float(input('Digite sua primeira nota: '))
n2 = float(input('Digite sua segunda nota: '))
m = (n1+n2)/2
print(f'A sua média foi {m:.1f}!')
if m >= 6.0:
    print('Parabéns, você atingiu a média!')
else:
    print('Você não atingiu a média, estude mais!')