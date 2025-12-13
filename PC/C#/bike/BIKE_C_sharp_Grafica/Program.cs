﻿using Org.BouncyCastle.Pqc.Crypto.Bike;
using Org.BouncyCastle.Security;
using System;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Globalization;

namespace BIKE_C_sharp_Grafica
{
    class Program
    {
        static void Main(string[] args)
        {
            CultureInfo.DefaultThreadCurrentCulture = new CultureInfo("en-US");
            CultureInfo.DefaultThreadCurrentUICulture = new CultureInfo("en-US");

            var versiones = new[] { "bike128", "bike192", "bike256" };


            foreach (var version in versiones)
            {
                Console.WriteLine($"\n--- Ejecutando pruebas para {version} ---");
                EjecutarPruebas(version, 1000);
            }

            Console.WriteLine("\n✅ Pruebas completadas.");
        }

        static void EjecutarPruebas(string version, int iteraciones)
        {
            var random = new SecureRandom();
            BikeKeyGenerationParameters parametros = version switch
            {
                "bike192" => new BikeKeyGenerationParameters(random, BikeParameters.bike192),
                "bike256" => new BikeKeyGenerationParameters(random, BikeParameters.bike256),
                _ => new BikeKeyGenerationParameters(random, BikeParameters.bike128),
            };


            var keyGen = new BikeKeyPairGenerator();
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
                var sw = Stopwatch.StartNew();
                var keyPair = keyGen.GenerateKeyPair();
                sw.Stop();
                var tKeyGen = sw.Elapsed.TotalMilliseconds;
                keygenTimes.Add(tKeyGen);

                var pub = (BikePublicKeyParameters)keyPair.Public;
                var priv = (BikePrivateKeyParameters)keyPair.Private;

                var kemGen = new BikeKemGenerator(random);
                sw.Restart();
                var encapsulated = kemGen.GenerateEncapsulated(pub);
                sw.Stop();
                var tEncaps = sw.Elapsed.TotalMilliseconds;
                encapsTimes.Add(tEncaps);

                var cipher = encapsulated.GetEncapsulation();

                var kemExt = new BikeKemExtractor(priv);
                sw.Restart();
                kemExt.ExtractSecret(cipher);
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

        static void MostrarEstadisticas(string etiqueta, List<double> tiempos)
        {
            var media = tiempos.Average();
            var std = Math.Sqrt(tiempos.Average(t => Math.Pow(t - media, 2)));
            Console.WriteLine($"--- {etiqueta} ---");
            Console.WriteLine($"Media: {media:F4} ms");
            Console.WriteLine($"Desviación estándar: {std:F4} ms");
        }
    }
}
