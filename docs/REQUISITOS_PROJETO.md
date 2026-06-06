# Definicao de Requisitos

> Fonte principal de requisitos do projeto, convertida de `_Requisitos_Projeto.docx` em 06/06/2026.
> O conteudo foi reorganizado em Markdown sem alterar as regras descritas no documento original.
> Decisoes posteriores confirmadas pela equipe prevalecem sobre trechos conflitantes deste documento.

## Decisoes Posteriores Confirmadas

- A recuperacao de senha por e-mail descrita no RF01 foi removida do escopo do projeto.

## Identificacao

- Projeto de POO
- Equipe: TechMind
- Membros:
  - Davi Wesley Monteiro Pereira
  - Jose Matheus Moreira Ferreira
  - Matheus Iven de Brito Valdevino
  - Joanderson Lima

## 1. Sumario

1. Introducao
2. Glossario
3. Definicao dos requisitos de usuario
4. Requisitos funcionais
5. Requisitos nao funcionais

## 2. Introducao

O descontrole financeiro contemporaneo e alimentado pela fragmentacao de pagamentos digitais, que tornam as despesas cotidianas menos perceptiveis. Este projeto visa solucionar essa "invisibilidade" financeira atraves de um sistema centralizado de gestao de fluxo de caixa. O diferencial desta solucao reside nao apenas no controle numerico, mas na correlacao entre o comportamento emocional e o consumo, permitindo que o usuario identifique gatilhos psicologicos que levam a gastos desnecessarios.

## 3. Glossario

- **Fluxo de Caixa:** Movimentacao de entrada (receitas) e saida (despesas) de dinheiro em um periodo.
- **Categorizacao Emocional:** Atribuicao de um estado subjetivo (ex.: felicidade, estresse) a uma transacao financeira.
- **Teto de Gastos:** Limite financeiro maximo estipulado pelo usuario para um periodo, geralmente mensal.
- **Modo Sobrevivencia:** Estado critico do sistema que restringe sugestoes de consumo a itens puramente essenciais.
- **Transacao Recorrente:** Despesa ou receita que se repete periodicamente, como aluguel ou assinatura de streaming.
- **Transacao:** Registro financeiro de entrada (receita) ou saida (despesa).
- **Categoria:** Classificacao de uma transacao, como Alimentacao ou Transporte.
- **Emocao:** Estado emocional associado a uma despesa.

## 4. Definicao dos Requisitos de Usuario

O sistema deve permitir que o usuario:

- Gerencie seu perfil de acesso de forma segura.
- Registre e visualize sua saude financeira de forma clara e centralizada.
- Entenda a relacao entre seus sentimentos e seus habitos de consumo.
- Receba auxilio proativo do sistema quando estiver prestes a comprometer seu orcamento mensal.
- Acesse a aplicacao a partir dos principais dispositivos eletronicos atuais, incluindo PCs, celulares e tablets.

## 5. Requisitos Funcionais

### RF01 - Gestao de Perfil

O sistema deve permitir que o usuario crie uma conta, autentique-se e gerencie seus dados pessoais com seguranca. O cadastro deve incluir nome, e-mail e senha, sendo obrigatorio validar o formato do e-mail e garantir sua unicidade. A senha deve atender criterios minimos de seguranca, como tamanho minimo e numero minimo de caracteres especiais e alfanumericos. O sistema deve permitir login e logout. Deve existir um mecanismo de recuperacao de senha via e-mail, utilizando tokens temporarios e unicos. O sistema deve impedir acessos indevidos por meio de bloqueio temporario apos multiplas tentativas invalidas e mensagens genericas para evitar exposicao de informacoes. Se a sessao expirar durante o uso, o usuario deve ser redirecionado para a tela de login sem perda de contexto critico.

### RF02 - Registro de Transacoes

O sistema deve permitir ao usuario registrar receitas e despesas informando valor, data e descricao. Cada transacao deve possuir um tipo (receita ou despesa), valor maior que zero e data valida. A descricao e opcional, mas limitada em tamanho, ate 256 caracteres. O usuario deve poder editar ou excluir transacoes, e qualquer alteracao deve refletir automaticamente nos relatorios e calculos do sistema.

### RF03 - Categorizacao Comum

O sistema deve permitir classificar transacoes em categorias pre-definidas e personalizadas. O usuario podera criar, editar e excluir categorias e subcategorias, desde que nao haja duplicidade de nomes. Caso uma categoria seja removida, o sistema deve solicitar a reclassificacao das transacoes associadas ou atribui-las a uma categoria padrao.

Categorias apresentadas na primeira lista do documento:

- Moradia
- Contas Residenciais
- Saude
- Educacao
- Alimentacao
- Transporte
- Cuidados Pessoais
- Hobbies
- Roupas
- Compras
- Lazer
- Investimentos
- Dividas
- Reserva de emergencia

Categorias pre-definidas para receitas:

- Salario
- Aposentadoria
- Pensao
- Aluguel
- Pro-labore
- Comissao/bonus
- Freelance
- Dividendos e juros
- Venda de itens

### RF04 - Categorizacao Emocional

O sistema deve permitir associar uma emocao a cada despesa registrada, podendo tambem associar uma emocao a avaliacao do gasto. A selecao da emocao deve ser opcional e baseada em uma lista pre-definida. Caso nenhuma emocao seja informada, a transacao deve ser marcada como "nao especificada". Essa funcionalidade servira como base para analises comportamentais futuras.

Emocoes pre-definidas:

- Calma
- Felicidade
- Raiva
- Frustracao
- Empolgacao
- Ansiedade
- Estresse
- Indiferenca
- Satisfacao
- Tedio

### RF05 - Teto de Gastos

O sistema deve permitir que o usuario defina limites financeiros mensais, tanto globais quanto por categoria, com cada limite condizente a sua categoria e os limites especificos condizentes com o limite global. Os limites devem ser configuraveis e editaveis a qualquer momento. Caso o usuario insira valores invalidos, como zero ou negativos, o sistema deve rejeitar a configuracao. O sistema deve recalcular automaticamente o estado financeiro quando houver alteracoes. Na ausencia de um limite definido, funcionalidades dependentes, como alertas, nao devem ser ativadas.

### RF06 - Alertas Criticos

O sistema deve monitorar os gastos e emitir notificacoes dentro da aplicacao quando o usuario atingir cada decimo do limite estabelecido. Os alertas devem ser enviados apenas uma vez por faixa de limite e devem refletir atualizacoes em tempo real conforme alteracoes nos dados. Se nao houver limite configurado, os alertas nao devem ser exibidos. Em caso de disparo instantaneo de varios alertas, apenas o mais alto e considerado.

### RF07 - Modo Sobrevivencia

O sistema deve ativar recomendacoes automaticas quando o usuario atingir uma porcentagem configurada, variando de 50% a 90%. As recomendacoes devem sugerir reducao de gastos em categorias consideradas nao essenciais, com base no historico do usuario, com foco naquelas com o maior limite superado. O sistema nao deve impor restricoes, apenas orientar o usuario. O sistema deve destacar visualmente as despesas marcadas como "Nao Essenciais" na tela principal e sugerir o bloqueio de novos lancamentos nessas categorias. Na ausencia de categorias nao essenciais, o sistema classifica automaticamente categorias como lazer, hobbies e compras.

### RF08 - Relatorios Visuais

O sistema deve gerar relatorios visuais em formato de graficos, como pizza e barras, para representar a distribuicao de gastos por categoria e por emocao. Os relatorios devem permitir filtros por periodo e categoria e devem ser atualizados automaticamente apos qualquer modificacao nos dados. Os relatorios devem incluir despesas infimas em uma unica fatia ou barra para evitar poluicao do grafico. O sistema so deve gerar um insight para uma emocao especifica apos o registro de, no minimo, cinco transacoes com aquela etiqueta no mes. Os relatorios devem incluir graficos de pizza da distribuicao percentual de categorias e emocoes nos gastos totais do mes e graficos de barra comparando os gastos nas dez principais categorias e emocoes. Informacoes de categorias e emocoes com menos dados serao expostas em forma textual em vez de graficos.

### RF09 - Cruzamento Emocao x Gasto

O sistema deve analisar a relacao entre emocoes e gastos, criando graficos que exponham a distribuicao de emocoes por categoria e mostrem os maiores gastos por emocao. O sistema deve calcular a media de gastos por emocao e comparar com a media geral do usuario. Se o gasto medio sob uma emocao, como Ansiedade, for 20% superior a media de gastos "Alegres" ou "Neutros", o sistema deve destacar isso como um "Gatilho de Gasto". Transacoes sem emocao vinculada devem ser agrupadas em uma categoria "Nao Informado" para nao distorcer as medias das emocoes registradas. Os resultados devem ser apresentados de forma compreensivel, evitando conclusoes quando nao houver dados suficientes ou estatisticamente relevantes.

### RF10 - Transacoes Recorrentes

O sistema deve permitir o agendamento automatico de transacoes recorrentes, como despesas fixas mensais. O usuario deve poder editar, pausar ou cancelar recorrencias sem afetar registros ja realizados. O sistema deve lidar com variacoes de calendario, como meses com menos dias.

### RF11 - Previsao de Saldo

O sistema deve calcular uma estimativa de saldo ao final do mes com base nas despesas fixas e no historico de gastos do usuario, baseando-se na media dos gastos dos ultimos tres meses ou menos. A previsao deve ser ajustada dinamicamente conforme novos dados sao inseridos, podendo indicar niveis de precisao.

### RF12 - Organizacao de Layout e Navegacao

O sistema deve ser estruturado em quatro areas principais e independentes, garantindo que as funcoes de autenticacao, registro e analise nao se misturem, facilitando o foco do usuario em cada tarefa.

- **Area de Acesso (Login/Cadastro):** porta de entrada do sistema. Uma pagina dedicada exclusivamente a identificacao do usuario, contendo campos para e-mail, senha e o botao de cadastro. Nao deve haver acesso ao conteudo financeiro ou ao menu principal antes da autenticacao bem-sucedida.
- **Area de Lancamentos (Despesas e Receitas):** pagina focada na operacao diaria. Deve exibir a lista de transacoes recentes e conter o formulario ou botao flutuante para insercao de novos registros (valor, data, categoria e emocao). O layout deve priorizar a leitura rapida do extrato.
- **Area de Inteligencia (Dashboards):** pagina visual dedicada a analise de longo prazo. Aqui devem ser concentrados todos os graficos de pizza, barras e os cruzamentos de sentimento divididos por mes. E uma area de consulta, separada da area de digitacao para evitar poluicao visual.
- **Sistema de Navegacao (Menu):** menu fixo, lateral em desktops ou barra inferior em dispositivos moveis, que permita a alternancia rapida entre a tela de Lancamentos, os Dashboards e as Configuracoes de Perfil/Layout.

## 6. Requisitos Nao Funcionais

### RNF 01 - Usabilidade

O sistema deve possuir uma hierarquia visual clara, onde o botao de novo registro seja o elemento de maior destaque, permitindo que o usuario complete um lancamento em no maximo tres interacoes.

### RNF 02 - Seguranca

O sistema deve exigir autenticacao por login e senha salvas com hash criptografico. Alem disso, e obrigatorio o uso de conexoes seguras (HTTPS) para evitar interceptacoes e a implementacao de validacoes rigorosas em todos os campos de digitacao, impedindo que usuarios mal-intencionados tentem inserir codigos ou textos gigantescos para quebrar o sistema.

### RNF 03 - Responsividade

A interface deve ser adaptavel ao dispositivo do usuario. O layout precisa se ajustar automaticamente para que o conteudo nao fique cortado ou pequeno demais em telas que variam de pequenos smartphones ate monitores de alta resolucao. No celular, os elementos interativos, como botoes e menus, devem ter um tamanho generoso para facilitar o toque com o polegar, enquanto no desktop as informacoes podem se expandir para aproveitar melhor o espaco lateral.

### RNF 04 - Desempenho

Operacoes comuns, como salvar um gasto ou abrir um grafico, devem ser concluidas em poucos segundos para evitar a sensacao de travamento. Para alcancar essa agilidade, o projeto deve utilizar componentes leves e tecnicas de carregamento progressivo, onde a estrutura da pagina aparece primeiro enquanto os dados mais pesados terminam de carregar em segundo plano.

### RNF 05 - Moeda

Todos os campos de entrada de valores devem possuir o simbolo "R$", pontos para milhares e virgulas para centavos conforme o usuario digita. Essa consistencia visual deve ser mantida em todos os relatorios e historicos, garantindo que o usuario sempre compreenda exatamente o valor que esta sendo manipulado.

### RNF 06 - Privacidade

O sistema deve garantir que as analises emocionais sejam usadas apenas para fins estatisticos pessoais. O projeto deve oferecer ao usuario o controle total sobre sua conta, permitindo a exclusao definitiva de todos os seus registros a qualquer momento.

### RNF 07 - Disponibilidade

O sistema precisa estar disponivel a todo momento e anunciar ao usuario uma mensagem de erro caso ocorra uma queda do sistema.

### RNF 08 - Manutenibilidade

O codigo deve ser escrito de forma legivel para seres humanos, utilizando nomes de funcoes e variaveis que expliquem sua propria finalidade. O uso de comentarios breves e a divisao do sistema em pequenos blocos independentes facilitam a correcao de erros e permitem que novos programadores entendam o funcionamento do software em pouco tempo.

### RNF 09 - Localizacao

Todos os gastos devem ser registrados com a data e hora corretas de Brasilia, evitando que transacoes feitas no final do dia aparecam no dia seguinte por erro de configuracao do servidor. Alem disso, a exibicao de datas deve seguir o formato nacional de dia, mes e ano, garantindo clareza total na leitura dos extratos.
