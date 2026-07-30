import nodemailer from "nodemailer";

export default async function handler(req, res) {
  if (req.method !== "POST") {
    return res.status(405).json({ error: "Método não permitido" });
  }

  const { conteudo } = req.body;

  try {
    const transporter = nodemailer.createTransport({
      service: "gmail",
      auth: {
        user: process.env.EMAIL_USER,
        pass: process.env.EMAIL_PASS
      }
    });

    await transporter.sendMail({
      from: process.env.EMAIL_USER,
      to: process.env.EMAIL_USER,
      subject: "Novo PMR Recebido",
      text: conteudo
    });

    return res.status(200).json({ sucesso: true });
  } catch (error) {
    console.error(error);
    return res.status(500).json({ error: "Erro ao enviar email" });
  }
}
