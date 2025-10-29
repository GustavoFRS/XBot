Trata-se de uma pipeline que extrai diariamente, dados dos PLs do site da câmara dos deputados, processando as informações com IA no meio do caminho. 

Uma coleção de Lambdas dentro de uma State Machine (Step Functions) cuida da parte de ETL, do scraping dos dados, passando por sua limpeza, processamento com a API da OpenAI e carregamento dos dados em um bucket S3

Essa State Machine é disparada de terça à sábado por meio do EventBridge, buscando os PLs do dia anterior. 
O EventBridge também aciona uma outra Lambda, que busca os objetos das postagens pendentes criados no Bucket S3, criando um cronograma no EventBridge Scheduler para cada postagem, com intervalo de X minutos entre elas.

Páginas do Bot:

Bluesky: https://bsky.app/profile/botdacamara.bsky.social
