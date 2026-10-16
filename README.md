# Zahrae Modas — Catálogo Feminino

Catálogo 100% focado em moda feminina, com finalização de pedidos via WhatsApp, arquitetura em nuvem (Vercel + Neon PostgreSQL + Cloudinary) e painel administrativo completo para gestão de produtos.

---

## 🛠️ Tecnologias Utilizadas

* **Backend:** Python / Flask
* **Banco de Dados:** PostgreSQL (Neon DB)
* **Hospedagem & Deployment:** Vercel (Serverless Functions)
* **Armazenamento de Imagens:** Cloudinary (upload dinâmico na nuvem)
* **Autenticação e Segurança:** Flask-Login, Flask-Limiter, ProxyFix, Werkzeug
* **Interface & UX:** HTML5, CSS3, JavaScript (Three.js para elementos 3D), animações microinterativas

---

## 🔑 Variáveis de Ambiente (Vercel)

Configuradas no painel da Vercel em **Settings > Environment Variables** (aplicadas para **Production**, **Preview** e **Development**):

```env
# Configurações do Flask
SECRET_KEY=sua_chave_secreta
DEBUG=0
PRODUCTION=1

# Banco de Dados (Neon PostgreSQL)
DATABASE_URL=postgresql://usuario:senha@ep-xyz.us-east-2.aws.neon.tech/neondb?sslmode=require

# Loja & Administrador
WHATSAPP_NUMERO=5592999999999  # Apenas números com DDD
ADMIN_EMAIL=seu_email@dominio.com
ADMIN_PASSWORD=sua_senha_segura

# Cloudinary (Hospedagem de Imagens)
CLOUDINARY_CLOUD_NAME=seu_cloud_name
CLOUDINARY_API_KEY=sua_api_key
CLOUDINARY_API_SECRET=seu_api_secret