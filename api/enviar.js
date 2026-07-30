import { put } from '@vercel/blob';

export default async function handler(req, res) {
  if (req.method !== "POST") {
    return res.status(405).json({ error: "Método não permitido" });
  }

  try {
    const { conteudo } = req.body;

    if (!conteudo) {
      return res.status(400).json({ error: "Conteúdo vazio" });
    }

    const agora = new Date();
    const nomeArquivo = `pmr/${agora.getFullYear()}-${agora.getMonth()+1}-${agora.getDate()}_${agora.getTime()}.pmr`;

    const blob = await put(nomeArquivo, conteudo, {
      access: 'public',
      contentType: 'text/plain'
    });

    return res.status(200).json({
      sucesso: true,
      url: blob.url
    });

  } catch (error) {
    console.error(error);
    return res.status(500).json({ error: "Erro ao salvar PMR" });
  }
}
