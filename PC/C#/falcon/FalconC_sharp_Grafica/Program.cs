static void Main(string[] args)
{
    if (args.Length < 2)
    {
        Console.WriteLine("Uso: FalconC_sharp_Grafica [Falcon512|Falcon1024] [pequeño|grande]");
        return;
    }

    var version = args[0];
    var tam = args[1];

    var mensaje = tam == "grande"
        ? new string('A', 10000)
        : "Mensaje pequeño para Falcon";

    var random = new SecureRandom();
    var parametros = version == "Falcon1024"
        ? new FalconKeyGenerationParameters(random, FalconParameters.falcon_1024)
        : new FalconKeyGenerationParameters(random, FalconParameters.falcon_512);

    var keyGen = new FalconKeyPairGenerator();
    keyGen.Init(parametros);
    var keyPair = keyGen.GenerateKeyPair();

    var priv = (FalconPrivateKeyParameters)keyPair.Private;
    var pub = (FalconPublicKeyParameters)keyPair.Public;

    var signer = new FalconSigner();
    signer.Init(true, priv);
    var sig = signer.GenerateSignature(System.Text.Encoding.UTF8.GetBytes(mensaje));

    var verifier = new FalconSigner();
    verifier.Init(false, pub);
    verifier.VerifySignature(System.Text.Encoding.UTF8.GetBytes(mensaje), sig);

    Console.WriteLine($"{version}-{tam} completado correctamente.");
}

