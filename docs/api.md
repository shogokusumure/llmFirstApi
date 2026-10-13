# API リファレンス

以下の仕様は FastAPI アプリケーションからビルド時に生成されます。API サーバーは公開されていないため、Swagger UI からのリクエスト送信はローカルで起動した API に対してのみ行ってください。

<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.17.14/swagger-ui.css">
<div id="swagger-ui"></div>
<script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.17.14/swagger-ui-bundle.js"></script>
<script>
  SwaggerUIBundle({
    url: "./openapi.json",
    dom_id: "#swagger-ui",
    deepLinking: true,
    supportedSubmitMethods: []
  });
</script>
