﻿using Org.BouncyCastle.Pqc.Crypto.Crystals.Dilithium;
using Org.BouncyCastle.Security;
using System;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Globalization;

namespace DilithiumC_sharp_Graficas
{
    class Program
    {
        static void Main(string[] args)
        {
            try
            {
                CultureInfo.DefaultThreadCurrentCulture = new CultureInfo("en-US");
                CultureInfo.DefaultThreadCurrentUICulture = new CultureInfo("en-US");

                var msg = "Hola, estamos en pruebas con el algoritmo pqc Crystals Dilithium";
                int iterations = 1000;

                var versions = new[] {"Dilithium2", "Dilithium3", "Dilithium5"};
                foreach (var version in versions)
                {
                    Console.WriteLine($"Ejecutando pruebas para {version}...");
                    RunDilithiumTests(version, msg, iterations);
                }
            }
            catch (Exception e)
            {
                Console.WriteLine("Error: " + e.Message);
            }
        }

        static void RunDilithiumTests(string method, string msg, int iterations)
        {
            var random = new SecureRandom();
            DilithiumKeyGenerationParameters keyGenParameters = method switch
            {
                "Dilithium3" => new DilithiumKeyGenerationParameters(random, DilithiumParameters.Dilithium3),
                "Dilithium5" => new DilithiumKeyGenerationParameters(random, DilithiumParameters.Dilithium5),
                _ => new DilithiumKeyGenerationParameters(random, DilithiumParameters.Dilithium2),
            };

            var keyPairGen = new DilithiumKeyPairGenerator();
            keyPairGen.Init(keyGenParameters);

            var keyGenTimes = new List<double>();
            var signTimes = new List<double>();
            var verifyTimes = new List<double>();
            double totalKeyGenTime = 0, totalSignTime = 0, totalVerifyTime = 0;

            var results = new List<string>();
            results.Add("Iteración,Dilithium Version,Tiempo Generación Claves,Tiempo Firma,Tiempo Verificación,Tiempo Total");

            for (int i = 0; i < 100; i++) // Warm-up
            {
                var keyPair = keyPairGen.GenerateKeyPair();
                var pub = (DilithiumPublicKeyParameters)keyPair.Public;
                var priv = (DilithiumPrivateKeyParameters)keyPair.Private;

                var signer = new DilithiumSigner();
                signer.Init(true, priv);
                var sig = signer.GenerateSignature(System.Text.Encoding.UTF8.GetBytes(msg));

                var verifier = new DilithiumSigner();
                verifier.Init(false, pub);
                verifier.VerifySignature(System.Text.Encoding.UTF8.GetBytes(msg), sig);
            }

            for (int i = 0; i < iterations; i++)
            {
                var sw = Stopwatch.StartNew();
                var keyPair = keyPairGen.GenerateKeyPair();
                sw.Stop();
                var keyGenTime = sw.Elapsed.TotalMilliseconds;
                keyGenTimes.Add(keyGenTime);
                totalKeyGenTime += keyGenTime;

                var pubKey = (DilithiumPublicKeyParameters)keyPair.Public;
                var privKey = (DilithiumPrivateKeyParameters)keyPair.Private;

                var signer = new DilithiumSigner();
                signer.Init(true, privKey);
                sw.Restart();
                var sig = signer.GenerateSignature(System.Text.Encoding.UTF8.GetBytes(msg));
                sw.Stop();
                var signTime = sw.Elapsed.TotalMilliseconds;
                signTimes.Add(signTime);
                totalSignTime += signTime;

                var verifier = new DilithiumSigner();
                verifier.Init(false, pubKey);
                sw.Restart();
                var result = verifier.VerifySignature(System.Text.Encoding.UTF8.GetBytes(msg), sig);
                sw.Stop();
                var verifyTime = sw.Elapsed.TotalMilliseconds;
                verifyTimes.Add(verifyTime);
                totalVerifyTime += verifyTime;

                var totalTime = keyGenTime + signTime + verifyTime;
                results.Add($"{i + 1},{method},{keyGenTime:F4},{signTime:F4},{verifyTime:F4},{totalTime:F4}");
            }

            var filename = $"{method}_performance2.csv";
            File.WriteAllLines(filename, results);
            Console.WriteLine($"Resultados exportados a '{filename}'.");

            PrintStatistics("Generación de Claves", keyGenTimes);
            PrintStatistics("Firma", signTimes);
            PrintStatistics("Verificación", verifyTimes);
            Console.WriteLine($"Promedios de {method}: KeyGen={totalKeyGenTime/iterations:F4} ms, Sign={totalSignTime/iterations:F4} ms, Verify={totalVerifyTime/iterations:F4} ms");
        }

        static void PrintStatistics(string name, List<double> values)
        {
            var avg = values.Average();
            var std = Math.Sqrt(values.Average(v => Math.Pow(v - avg, 2)));
            Console.WriteLine($"--- {name} ---");
            Console.WriteLine($"Media: {avg:F4} ms");
            Console.WriteLine($"Desviación estándar: {std:F4} ms");
            Console.WriteLine();
        }
    }
}
