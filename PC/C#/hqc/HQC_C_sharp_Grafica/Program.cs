﻿using System;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using Org.BouncyCastle.Pqc.Crypto.Hqc;
using Org.BouncyCastle.Security;
using System.Globalization;

namespace HQC_C_sharp_Grafica
{
    class Program
    {
        static void Main(string[] args)
        {
            CultureInfo.DefaultThreadCurrentCulture = new CultureInfo("en-US");
            CultureInfo.DefaultThreadCurrentUICulture = new CultureInfo("en-US");

            var versiones = new[] { "hqc128", "hqc192", "hqc256" };

            foreach (var version in versiones)
            {
                Console.WriteLine($"\n--- Ejecutando pruebas para {version} ---");
                EjecutarPruebas(version, 1000);
            }

            Console.WriteLine("\n✅ Todas las pruebas finalizadas.");
        }

        static void EjecutarPruebas(string version, int iteraciones)
        {
            var random = new SecureRandom();
            HqcKeyGenerationParameters parametros = version switch
            {
                "hqc192" => new HqcKeyGenerationParameters(random, HqcParameters.hqc192),
                "hqc256" => new HqcKeyGenerationParameters(random, HqcParameters.hqc256),
                _ => new HqcKeyGenerationParameters(random, HqcParameters.hqc128),
            };

            var keyGen = new HqcKeyPairGenerator();
            keyGen.Init(parametros);

            var keygenTimes = new List<double>();
            var encapsTimes = new List<double>();
            var decapsTimes = new List<double>();
            var totalTimes = new List<double>();

            var csvName = $"{version}_performance.csv";
            using var writer = new StreamWriter(csvName);
            writer.WriteLine("Iteración,Versión,Tiempo KeyGen,Tiempo Encapsulación,Tiempo Decapsulación,Tiempo Total");

            for (int i = 0; i < iteraciones; i++)
            {
                // KeyGen
                var sw = Stopwatch.StartNew();
                var keyPair = keyGen.GenerateKeyPair();
                sw.Stop();
                var tKeyGen = sw.Elapsed.TotalMilliseconds;
                keygenTimes.Add(tKeyGen);

                var pubKey = (HqcPublicKeyParameters)keyPair.Public;
                var privKey = (HqcPrivateKeyParameters)keyPair.Private;

                // Encapsulación
                var kemGen = new HqcKemGenerator(random);
                sw.Restart();
                var encapsulated = kemGen.GenerateEncapsulated(pubKey);
                sw.Stop();
                var tEncaps = sw.Elapsed.TotalMilliseconds;
                encapsTimes.Add(tEncaps);

                var ciphertext = encapsulated.GetEncapsulation();

                // Decapsulación
                var kemExt = new HqcKemExtractor(privKey);
                sw.Restart();
                kemExt.ExtractSecret(ciphertext);
                sw.Stop();
                var tDecaps = sw.Elapsed.TotalMilliseconds;
                decapsTimes.Add(tDecaps);

                var tTotal = tKeyGen + tEncaps + tDecaps;
                totalTimes.Add(tTotal);

                writer.WriteLine($"{i + 1},{version},{tKeyGen:F4},{tEncaps:F4},{tDecaps:F4},{tTotal:F4}");
            }

            Console.WriteLine($"📄 Resultados exportados a '{csvName}'");
            MostrarEstadisticas("KeyGen", keygenTimes);
            MostrarEstadisticas("Encapsulación", encapsTimes);
            MostrarEstadisticas("Decapsulación", decapsTimes);
        }

        static void MostrarEstadisticas(string label, List<double> tiempos)
        {
            var avg = tiempos.Average();
            var std = Math.Sqrt(tiempos.Average(t => Math.Pow(t - avg, 2)));
            Console.WriteLine($"--- {label} ---");
            Console.WriteLine($"Media: {avg:F4} ms");
            Console.WriteLine($"Desviación estándar: {std:F4} ms");
        }
    }
}
