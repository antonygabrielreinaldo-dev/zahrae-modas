# Zahrae Modas — Catálogo feminino (Flask)

Catálogo 100% moda feminina, com compra pelo WhatsApp e painel do lojista.

## Rodar
```
py -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
py app.py
```

## Já tem o banco antigo (zaraeh.db)?
Copie seu `zaraeh.db` para esta pasta e rode **uma vez**: `py migrar_para_feminino.py`
(ele remove produtos masculinos/infantis após confirmação e reclassifica o resto).

## Fotos
Coloque em `static/img/`: `produto-1.jpg`… (proporção 3:4) e `hero.jpg` (foto da home, opcional — formato vertical 4:5).
Pelo admin (`/admin/produtos`) o upload já nomeia o arquivo sozinho.

## Segurança

## Logo
Os arquivos do logo estão em `static/img/` (`logo-full.png`, `logo-wordmark.png`, `logo-star.png`, `favicon.png`). Todas as páginas internas têm o botão **Voltar**, e o menu tem **Início**.

## Movimento e microinterações
Linguagem única: elementos "sobem e assentam" (ease-out), hover eleva 2–3px, clique afunda 1px com ondulação, entradas ao rolar têm stagger.
Tudo respeita "reduzir movimento". Itens: botões com 6 estados (incl. loading), campos com foco/preenchido/erro, menu mobile animado, diálogo de confirmação, toasts, barra de progresso ao navegar, transição entre páginas, zoom na foto do produto, botão voltar ao topo.
A estrela e o nome ZAHRAE em 3D ficam em `static/js/star3d.js` (textura `static/img/logo-wordmark-3d.png`).
