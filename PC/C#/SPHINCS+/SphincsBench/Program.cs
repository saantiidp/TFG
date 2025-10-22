using System;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using Org.BouncyCastle.Security;
using Org.BouncyCastle.Pqc.Crypto.SphincsPlus;

class Program
{
    static void Main(string[] args)
    {
        // Defaults
        int ITER = 100;
        string variant = null;

        // Back-compat: si el 1er arg es número, es ITER
        if (args.Length > 0 && int.TryParse(args[0], out var itBackCompat))
            ITER = itBackCompat;

        // Parse flags
        for (int i = 0; i < args.Length; i++)
        {
            switch (args[i])
            {
                case "--variant":
                    if (i + 1 >= args.Length) throw new ArgumentException("--variant requiere un valor");
                    variant = args[++i].Trim().ToLowerInvariant();
                    break;
                case "--iterations":
                case "-n":
                    if (i + 1 >= args.Length) throw new ArgumentException("--iterations/-n requiere un número");
                    if (!int.TryParse(args[++i], out ITER)) throw new ArgumentException("iteraciones no válidas");
                    break;
            }
        }

        CultureInfo.DefaultThreadCurrentCulture = CultureInfo.InvariantCulture;
        CultureInfo.DefaultThreadCurrentUICulture = CultureInfo.InvariantCulture;

        var suites = new (string Name, SphincsPlusParameters Param)[]
        {
            // SHA2
            ("sha2-128s", SphincsPlusParameters.sha2_128s),
            ("sha2-128f", SphincsPlusParameters.sha2_128f),
            ("sha2-192s", SphincsPlusParameters.sha2_192s),
            ("sha2-192f", SphincsPlusParameters.sha2_192f),
            ("sha2-256s", SphincsPlusParameters.sha2_256s),
            ("sha2-256f", SphincsPlusParameters.sha2_256f),
            // SHAKE
            ("shake-128s", SphincsPlusParameters.shake_128s),
            ("shake-128f", SphincsPlusParameters.shake_128f),
            ("shake-192s", SphincsPlusParameters.shake_192s),
            ("shake-192f", SphincsPlusParameters.shake_192f),
            ("shake-256s", SphincsPlusParameters.shake_256s),
            ("shake-256f", SphincsPlusParameters.shake_256f),
        };

        IEnumerable<(string Name, SphincsPlusParameters Param)> target =
            string.IsNullOrEmpty(variant)
            ? suites
            : suites.Where(s => s.Name.Equals(variant, StringComparison.OrdinalIgnoreCase));

        if (!target.Any())
            throw new ArgumentException($"Variante no reconocida: {variant}");

        var rng = new SecureRandom();
        var msg = System.Text.Encoding.UTF8.GetBytes("Mensaje de prueba para SPHINCS+");

        foreach (var s in target)
        {
            string csv = $"{s.Name}_performance.csv";
            using var w = new StreamWriter(csv);
            w.WriteLine("Iteración,SPHINCS+ Version,Tiempo Generación Claves,Tiempo Firma,Tiempo Verificación,Tiempo Total");

            var kpg = new SphincsPlusKeyPairGenerator();
            kpg.Init(new SphincsPlusKeyGenerationParameters(rng, s.Param));

            var keyTimes = new List<double>();
            var signTimes = new List<double>();
            var verifyTimes = new List<double>();

            Console.WriteLine($"\n== {s.Name} ==  (ITER={ITER})");
            for (int i = 1; i <= ITER; i++)
            {
                var swTotal = Stopwatch.StartNew();

                var sw = Stopwatch.StartNew();
                var kp = kpg.GenerateKeyPair();
                sw.Stop();
                double tKey = sw.Elapsed.TotalMilliseconds;

                var signer = new SphincsPlusSigner();
                signer.Init(true, kp.Private);
                sw.Restart();
                var sig = signer.GenerateSignature(msg);
                sw.Stop();
                double tSign = sw.Elapsed.TotalMilliseconds;

                var verifier = new SphincsPlusSigner();
                verifier.Init(false, kp.Public);
                sw.Restart();
                bool ok = verifier.VerifySignature(msg, sig);
                sw.Stop();
                if (!ok) throw new Exception("Verificación fallida.");
                double tVerify = sw.Elapsed.TotalMilliseconds;

                swTotal.Stop();
                double tTotal = swTotal.Elapsed.TotalMilliseconds;

                keyTimes.Add(tKey);
                signTimes.Add(tSign);
                verifyTimes.Add(tVerify);

                w.WriteLine($"{i},{s.Name},{tKey:F4},{tSign:F4},{tVerify:F4},{tTotal:F4}");
            }

            PrintStats("KeyGen", keyTimes);
            PrintStats("Sign", signTimes);
            PrintStats("Verify", verifyTimes);
            Console.WriteLine($"CSV -> {csv}");
        }
    }

    static void PrintStats(string label, List<double> xs)
    {
        double avg = xs.Average();
        double std = Math.Sqrt(xs.Average(v => Math.Pow(v - avg, 2)));
        Console.WriteLine($"{label}: {avg:F4} ms (±{std:F4})");
    }
}
