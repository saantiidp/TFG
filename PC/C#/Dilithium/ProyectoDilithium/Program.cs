using System;
using Org.BouncyCastle.Crypto.Parameters;
using Org.BouncyCastle.Crypto.Signers;
using Org.BouncyCastle.Crypto;
using Org.BouncyCastle.Security;

class Program
{
    static void Main()
    {
        var random = new SecureRandom();

        // 1. Inicializar generador de claves Dilithium3
        var keyGen = new Org.BouncyCastle.Crypto.Generators.DilithiumKeyPairGenerator();
        keyGen.Init(new DilithiumKeyGenerationParameters(random, DilithiumParameters.Dilithium3));
        AsymmetricCipherKeyPair keyPair = keyGen.GenerateKeyPair();

        var pub = (DilithiumPublicKeyParameters)keyPair.Public;
        var priv = (DilithiumPrivateKeyParameters)keyPair.Private;

        Console.WriteLine("Clave pública: " + Convert.ToBase64String(pub.GetEncoded()));
        Console.WriteLine("Clave privada: " + Convert.ToBase64String(priv.GetEncoded()));

        // 2. Firmar un mensaje
        byte[] mensaje = System.Text.Encoding.UTF8.GetBytes("Hola desde C# con Dilithium!");
        var signer = new DilithiumSigner();
        signer.Init(true, priv);
        signer.BlockUpdate(mensaje, 0, mensaje.Length);
        byte[] firma = signer.GenerateSignature();

        Console.WriteLine("Firma: " + Convert.ToBase64String(firma));

        // 3. Verificar la firma
        var verifier = new DilithiumSigner();
        verifier.Init(false, pub);
        verifier.BlockUpdate(mensaje, 0, mensaje.Length);
        bool esValida = verifier.VerifySignature(firma);

        Console.WriteLine("¿Firma válida? " + esValida);
    }
}

