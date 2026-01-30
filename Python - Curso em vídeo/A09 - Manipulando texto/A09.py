frase = 'Curso em Vídeo Python'
print(frase [0:14:1])
#Fatiamento - 1º indique onde quer começar, 2º indique até onde fatiar, 3º pode ser usado para pular, por exemplo de 2 em 2.
frase.count('o')
print(f'A letra "o" aparece {frase.count("o")} vezes!')
print(len(frase)) #Para contar quantos espaços tem a str, podendo usar o comando "frase.strip()" para retirar os espaços antes e depois da str.
print(frase.replace('Python', 'Programação')) #Dessa forma, eu alterei as palavras somente no comando, para efetivar a troca deveria ser:
frase = frase.replace('Python', 'Programação')
print(frase)
print('Curso' in frase) #(True or False), se a palavra existe ou não na str.
print(frase.find('Vídeo')) #Qual posição da str está a palavra?
#frase.upper ou .lower para passar para minúsculo ou maiúsculo.
print(frase.find('em')) #Para dizer em qual posição começa a palavra.
print(frase.capitalize()) #Deixa maiúscula somente a primeira letra da str.
print(frase.title()) #Deixa maiúscula a primeira letra de todas as palavras da str, reconhecendo pelos espaços.
print(frase.split()) #Para separar a str em várias str's por cada ' ' separação entre palavras.
print(''.join(frase)) #Acima, utilizando o SPLIT, separamos a str em várias outras, conforme seu número de palavras. Utilizando o JOIN, a gente junta as str's novamente.
print("""Boa noite! Que alegria encerrar o dia conversando com você.
Espero que o seu descanso seja profundo e revigorante. Que você possa deixar de lado todas as preocupações de hoje e apenas relaxar, permitindo que sua mente se acalme para sonhar com coisas boas.
Você merece uma noite de paz e um sono bem quentinho. Durma bem e acorde com as energias renovadas para o amanhã! ✨🌙""")